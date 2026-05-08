## Complete SRE Formula Sheet (Interview Ready)

---

## 1. AVAILABILITY & DOWNTIME

### Uptime / Availability

```python
# SLI: Actual measured availability
SLI_availability = (Total_time - Downtime) / Total_time * 100

# Example: 43,200 min month, 43 min downtime
# SLI = (43200 - 43) / 43200 * 100 = 99.9%
```

### Downtime from Availability

```python
# Total downtime in time units
Downtime = Total_time * (1 - Availability_percentage / 100)

# Example: 30 days, 99.9% availability
# Downtime = 43200 * (1 - 0.999) = 43.2 minutes
```

---

## 2. ERROR BUDGET

### Total Allowed Error Budget (The Limit)

```python
# Maximum downtime allowed by SLO
Allowed_error_budget_time = Total_time * (1 - SLO_percentage / 100)

# Example: 99.9% SLO in 30 days
# Allowed = 43200 * 0.001 = 43.2 minutes
```

### Consumed Error Budget (Used So Far)

```python
# How much budget you've already used
Consumed_error_budget = Total_time * (1 - SLI_percentage / 100)

# Or
Consumed_error_budget = Actual_downtime_so_far

# Example: SLI = 99.85% in 15 days
# Consumed = 21600 * 0.0015 = 32.4 minutes
```

### Remaining Error Budget

```python
# Budget left before SLO breach
Remaining_error_budget = Total_time * (SLO_percentage - SLI_percentage) / 100

# Example: SLO=99.9%, SLI=99.85%
# Remaining = 43200 * (0.001) = 43.2 minutes? NO! Wait carefully:

# CORRECT:
SLO = 99.9% = 0.999
SLI = 99.85% = 0.9985
Remaining = 43200 * (0.999 - 0.9985) = 43200 * 0.0005 = 21.6 minutes
```

### Error Budget Burn Rate

```python
# How fast you're consuming budget
Burn_rate = Consumed_error_budget / Time_elapsed

# Example: Used 30 minutes in 15 days
# Burn_rate = 30 / (15 * 1440) = 0.00139 minutes per minute

# Or as percentage of month
Burn_rate_pct = (Consumed / Allowed) / (Time_elapsed / Total_time)

# Example: Used 70% of budget in 50% of month
# Burn_rate = 0.70 / 0.50 = 1.4 (burning 40% faster than allowed)
```

---

## 3. MTTR, MTBF, MTTF, MTTA

### MTTR (Mean Time To Repair)

```python
# Average time to FIX a failure
MTTR = Total_repair_time / Number_of_incidents

# What's included: detection → diagnosis → mitigation → resolution
# Example: 3 incidents took 10, 20, 30 min to fix
# MTTR = (10+20+30) / 3 = 20 minutes
```

### MTBF (Mean Time Between Failures)

```python
# Average time between failures (uptime between incidents)
MTBF = Total_uptime / Number_of_failures

# Example: System ran 1000 hours, failed 5 times
# MTBF = 1000 / 5 = 200 hours between failures
```

### MTTF (Mean Time To Failure)

```python
# Average time until a NON-repairable system fails
MTTF = Total_operating_time / Number_of_failures

# Use when: Components that get replaced, not repaired (e.g., hard drives)
```

### MTTA (Mean Time To Acknowledge)

```python
# Average time from alert firing to someone acknowledging it
MTTA = Total_acknowledgment_time / Number_of_alerts

# Example: 3 alerts took 2, 5, 3 min to acknowledge
# MTTA = (2+5+3)/3 = 3.33 minutes
```

### The Relationship

```python
# For repairable systems:
MTBF = MTTR + MTTF  # Usually MTTR is small, so MTBF ≈ MTTF

# Availability from MTBF and MTTR:
Availability = MTBF / (MTBF + MTTR) * 100

# Example: MTBF=200 hours, MTTR=0.5 hours
# Availability = 200/(200.5) = 99.75%
```

---

## 4. RTO & RPO (Disaster Recovery)

### RTO (Recovery Time Objective)

```python
# Maximum acceptable time to RESTORE service after disaster
# Answer: "How fast must we be back up?"

RTO = Target_time_to_recover

# Example: RTO = 4 hours
# Meaning: System must be fully functional within 4 hours of disaster
```

### RPO (Recovery Point Objective)

```python
# Maximum acceptable data LOSS measured in time
# Answer: "How much data can we afford to lose?"

RPO = Maximum_age_of_data_after_recovery

# Example: RPO = 1 hour
# Meaning: Lose at most 1 hour of data (backups every hour)
```

### RTO vs RPO Comparison

```python
# Scenario: E-commerce database disaster at 10:00 AM
RTO = 2 hours   # System must be back by 12:00 PM
RPO = 15 minutes # Can only lose data from 9:45 AM to 10:00 AM

# Lower RTO = More expensive (hot standby, multi-region)
# Lower RPO = More frequent backups (streaming replication)
```

### Availability from RTO

```python
# Availability target implying RTO
Availability = (Total_time - RTO) / Total_time * 100

# Example: RTO = 4 hours in 30-day month
# Availability = (720 - 4) / 720 * 100 = 99.44%
# This is for the disaster scenario, not normal operations!
```

---

## 5. SLI, SLO, SLA Relationship

### Success Rate SLI

```python
# For request-based services
SLI_success_rate = (Successful_requests / Total_requests) * 100

# Example: 1,000,000 requests, 999,000 success
# SLI = 999000/1000000 * 100 = 99.9%
```

### Latency SLI (p99)

```python
# Percentage of requests below threshold
SLI_latency = (Requests_below_threshold / Total_requests) * 100

# Example: 95% of requests under 200ms
# SLI = 95%
```

### SLO to Allowed Failures

```python
# For request-based SLO
Allowed_failures = Total_requests * (1 - SLO_percentage / 100)

# Example: 10M requests, 99.9% SLO
# Allowed_failures = 10,000,000 * 0.001 = 10,000 failures
```

---

## 6. Composite Formulas

### Downtime from MTTR and Frequency

```python
# Total downtime in period
Downtime = Number_of_incidents * MTTR

# Or
Downtime = Incident_rate * Time_period * MTTR
# Where Incident_rate = incidents per hour
```

### Availability from MTTR and MTBF

```python
Availability = MTBF / (MTBF + MTTR) * 100

# Example: MTBF=100 hours, MTTR=1 hour
# Availability = 100/101 = 99.01%
```

### Required MTTR to Meet SLO

```python
# Given allowed downtime and expected incidents
Required_MTTR = Allowed_downtime / Expected_incidents

# Example: SLO 99.9% in 30 days = 43 min allowed, expect 5 incidents
# Required_MTTR = 43 / 5 = 8.6 minutes
```

---

## 7. Complete Cheat Sheet Table

| Formula | Purpose | Example |
|---------|---------|---------|
| `SLI = (Total - Downtime)/Total × 100` | Actual availability | 99.9% |
| `Allowed downtime = Total × (1 - SLO/100)` | Error budget limit | 43 min |
| `Consumed budget = Total × (1 - SLI/100)` | Used so far | 30 min |
| `Remaining = Total × (SLO - SLI)/100` | Leftover | 13 min |
| `MTTR = Repair time sum ÷ Incidents` | Fix speed | 15 min |
| `MTBF = Uptime ÷ Failures` | Time between failures | 200 hours |
| `MTTA = Acknowledge time sum ÷ Alerts` | Alert response | 3 min |
| `RTO = Max time to restore` | Disaster recovery target | 4 hours |
| `RPO = Max data loss time` | Backup frequency target | 1 hour |
| `Availability = MTBF/(MTBF+MTTR)` | From reliability metrics | 99.75% |
| `Burn rate = Consumed/Allowed ÷ Time_elapsed/Total` | Budget consumption speed | 1.4 |
| `Required MTTR = Allowed downtime ÷ Expected incidents` | Planning | 8.6 min |

---

## 8. Interview One-Liners

### MTTR
> *"MTTR is average time to repair = total repair time divided by number of incidents. It directly impacts availability SLI."*

### RTO vs RPO
> *"RTO is how fast we restore service. RPO is how much data we can lose. RTO=4 hours, RPO=1 hour means back up in 4 hours losing at most 1 hour of data."*

### Error Budget
> *"Error budget = total time × (1 - SLO). It's the maximum downtime allowed before breaching SLO."*

### Burn Rate
> *"Burn rate = budget consumed percentage ÷ time elapsed percentage. >1 means we'll breach SLO before period ends."*

---

## Quick Memory Trick

```
RTO = Time to RESTORE (clock starts at disaster)
RPO = Point of recovery (how far back we go)

MTTR = Fix speed (small incidents)
RTO = Disaster recovery speed (big incidents)

MTBF = How long between oopses
MTTF = How long until death (non-repairable)
```
