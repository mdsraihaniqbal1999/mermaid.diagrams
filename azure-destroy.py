"""
Azure Resource Group Scanner & Cleaner
========================================
This script deletes resource groups unless they have a "no-destroy: true" tag.

What it does:
  1. Logs into Azure using your service principal
  2. Finds all your active subscriptions  
  3. Looks at every resource group in each subscription
  4. Checks if the resource group has the safety tag "no-destroy: true"
  5. If the tag is there → leaves it alone (safe!)
  6. If the tag is missing → deletes the whole resource group and everything inside it

Before running, install:
    pip install azure-identity azure-mgmt-resource azure-mgmt-subscription
"""

import sys
import time
import logging
from datetime import datetime

try:
    from azure.identity import ClientSecretCredential
    from azure.mgmt.resource import ResourceManagementClient
    from azure.mgmt.subscription import SubscriptionClient
    from azure.core.exceptions import HttpResponseError
except ImportError:
    print("You need to run: pip install azure-identity azure-mgmt-resource azure-mgmt-subscription")
    sys.exit(1)

#Credentials
TENANT_ID     = ""
CLIENT_ID     = ""
CLIENT_SECRET = ""

# The safety tag that protects a resource group from being deleted
# If a resource group has this tag, we leave it alone
PROTECTION_TAG_KEY   = "no-destroy"
PROTECTION_TAG_VALUE = "true"

# Set this to True if you just want to see what would happen (no actual deletion)
DRY_RUN = True


# Set up logging so we have a record of everything
LOG_FILE = f"azure_cleaner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE),
    ],
)
log = logging.getLogger(__name__)


# -------------------------------------------------
# Helper function: Check if a resource group is protected
# -------------------------------------------------
def is_protected(tags: dict) -> bool:
    """Returns True if the resource group has the no-destroy: true tag"""
    if not tags:
        return False
    
    # Look through all the tags on the resource group
    for key, value in tags.items():
        # Check if the tag matches our protection tag (case doesn't matter)
        if key.lower() == PROTECTION_TAG_KEY.lower():
            if PROTECTION_TAG_VALUE == "" or value.lower() == PROTECTION_TAG_VALUE.lower():
                return True  # Found the protection tag, so this RG is safe
    return False  # No protection tag found, so this RG can be deleted


# -------------------------------------------------
# Helper function: Make tags look pretty when printing
# -------------------------------------------------
def display_tags(tags: dict) -> str:
    """Turn tags into a readable string for logging"""
    if not tags:
        return "(no tags)"
    return "  |  ".join(f"{k} = {v}" for k, v in tags.items())


# -------------------------------------------------
# Step 1: Log into Azure
# -------------------------------------------------
def login_to_azure() -> ClientSecretCredential:
    """Authenticate using service principal credentials"""
    log.info(f"Logging into Azure with client ID: {CLIENT_ID}...")
    try:
        credentials = ClientSecretCredential(
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        )
        log.info("Successfully logged into Azure!")
        return credentials
    except Exception as error:
        log.error(f"Login failed: {error}")
        sys.exit(1)


# -------------------------------------------------
# Step 2: Find all active subscriptions
# -------------------------------------------------
def find_subscriptions(credentials) -> list:
    """Get a list of all enabled subscriptions"""
    subscription_client = SubscriptionClient(credentials)
    active_subs = []

    log.info("")
    log.info("=" * 60)
    log.info("  STEP 1 — FINDING ALL ACTIVE SUBSCRIPTIONS")
    log.info("=" * 60)

    for sub in subscription_client.subscriptions.list():
        # Check if this subscription is active/enabled
        state = sub.state.value.lower() if hasattr(sub.state, "value") else str(sub.state).lower()
        
        if state != "enabled":
            log.info(f"  SKIPPING (disabled subscription): {sub.display_name} [{sub.subscription_id}]")
            continue
            
        log.info(f"  ✓ ACTIVE: {sub.display_name} [{sub.subscription_id}]")
        active_subs.append((sub.subscription_id, sub.display_name))

    log.info(f"  Found {len(active_subs)} active subscription(s)")
    return active_subs


# -------------------------------------------------
# Step 3: Scan and clean a single subscription
# -------------------------------------------------
def clean_subscription(credentials, subscription_id: str, subscription_name: str, stats: dict):
    """Look at every resource group in a subscription and delete unprotected ones"""
    log.info("")
    log.info("=" * 60)
    log.info(f"  SUBSCRIPTION: {subscription_name}")
    log.info(f"  ID: {subscription_id}")
    log.info("=" * 60)

    # Create a client for managing resources in this subscription
    resource_client = ResourceManagementClient(credentials, subscription_id)

    # Get all resource groups in this subscription
    try:
        resource_groups = list(resource_client.resource_groups.list())
    except HttpResponseError as error:
        log.error(f"  Could not list resource groups: {error.message}")
        stats["errors"] += 1
        return

    if not resource_groups:
        log.info("  No resource groups found in this subscription")
        return

    log.info(f"  Found {len(resource_groups)} resource group(s)")

    # Look at each resource group one by one
    for rg in resource_groups:
        rg_name = rg.name
        rg_tags = rg.tags or {}

        log.info("")
        log.info("  " + "─" * 50)
        log.info(f"  Resource Group: {rg_name}")
        log.info(f"  Location: {rg.location}")
        log.info(f"  Tags: {display_tags(rg_tags)}")

        # Find all resources inside this resource group
        try:
            resources = list(resource_client.resources.list_by_resource_group(rg_name))
        except HttpResponseError as error:
            log.error(f"  ERROR listing resources: {error.message}")
            resources = []

        # Show what resources are inside
        if resources:
            log.info(f"  Contains {len(resources)} resource(s):")
            for res in resources:
                log.info(f"    • {res.name} [{res.type}]")
        else:
            log.info("  Contains no resources (empty)")

        # Check if this resource group is protected
        if is_protected(rg_tags):
            log.info(f"  DECISION: 🛡️  Resource group has '{PROTECTION_TAG_KEY}: {PROTECTION_TAG_VALUE}' - KEEPING IT SAFE")
            stats["kept"] += 1
        else:
            log.info(f"  DECISION: 💀 No protection tag found - DELETE THIS RESOURCE GROUP")
            stats["to_delete"] += 1

            if DRY_RUN:
                log.info(f"  DRY RUN MODE: Would delete '{rg_name}' and its {len(resources)} resource(s)")
            else:
                log.info(f"  Deleting '{rg_name}' right now...")
                try:
                    # Start the deletion and wait for it to finish
                    deletion_poller = resource_client.resource_groups.begin_delete(rg_name)
                    deletion_poller.result()  # This waits until deletion is complete
                    log.info(f"  ✓ Successfully deleted: {rg_name}")
                    stats["deleted"] += 1
                except HttpResponseError as error:
                    log.error(f"  ✗ Failed to delete {rg_name}: {error.message}")
                    stats["errors"] += 1
                except Exception as error:
                    log.error(f"  ✗ Unexpected error deleting {rg_name}: {error}")
                    stats["errors"] += 1

        log.info("  " + "─" * 50)


# -------------------------------------------------
# Ask for confirmation before doing anything destructive
# -------------------------------------------------
def get_confirmation() -> bool:
    """Make sure the user really wants to delete things"""
    print("\n" + "=" * 60)
    print("  ⚠️  WARNING: This script will DELETE unprotected resource groups")
    print(f"  Protection tag: {PROTECTION_TAG_KEY} = {PROTECTION_TAG_VALUE or '<any value>'}")
    print(f"  Log file: {LOG_FILE}")
    print("  Any resource group WITHOUT this tag will be DELETED FOREVER")
    print("=" * 60)
    answer = input('  Type "YES DELETE" to continue, anything else to stop: ').strip()
    return answer == "YES DELETE"


# -------------------------------------------------
# Main function - where everything starts
# -------------------------------------------------
def main():
    # Make sure the user filled in their Azure credentials
    if TENANT_ID == "YOUR_TENANT_ID":
        log.error("Please edit the script and add your TENANT_ID, CLIENT_ID, and CLIENT_SECRET")
        sys.exit(1)

    # If we're doing a real deletion, ask for confirmation
    if not DRY_RUN:
        if not get_confirmation():
            log.info("Operation cancelled by user")
            sys.exit(0)
    else:
        log.info("DRY RUN MODE ENABLED - No resources will actually be deleted")
        log.info("Set DRY_RUN = False when you're ready to delete for real")

    # Log in and get ready
    credentials = login_to_azure()
    subscriptions = find_subscriptions(credentials)

    if not subscriptions:
        log.warning("No active subscriptions found. Exiting.")
        sys.exit(0)

    # Track our progress
    stats = {"to_delete": 0, "deleted": 0, "kept": 0, "errors": 0}
    start_time = time.time()

    # Go through each subscription and clean it
    for sub_id, sub_name in subscriptions:
        try:
            clean_subscription(credentials, sub_id, sub_name, stats)
        except Exception as error:
            log.error(f"Something went wrong in subscription {sub_id}: {error}")
            stats["errors"] += 1

    # Show the final results
    elapsed_time = time.time() - start_time

    log.info("")
    log.info("=" * 60)
    log.info(f"  SUMMARY - {'DRY RUN' if DRY_RUN else 'LIVE DELETION'}")
    log.info("=" * 60)
    log.info(f"  Resource groups protected (kept):  {stats['kept']}")
    log.info(f"  Resource groups marked for deletion: {stats['to_delete']}")
    log.info(f"  Resource groups actually deleted:   {stats['deleted']}")
    log.info(f"  Errors encountered:                 {stats['errors']}")
    log.info(f"  Time taken: {elapsed_time:.1f} seconds")
    log.info(f"  Full log saved to: {LOG_FILE}")
    log.info("=" * 60)

    # Exit with error code if we had problems
    sys.exit(1 if stats["errors"] else 0)


# Run the script
if __name__ == "__main__":
    main()