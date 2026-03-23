---
name: odoo-queue-job-patterns
description: OCA queue_job async job patterns — use when adding asynchronous background job execution, configuring job channels or priorities, handling job failures and retries, or understanding dev vs prod job behavior.
---

# OCA Queue Job Patterns

## Basic Usage

```python
from odoo.addons.queue_job.job import job

class MyModel(models.Model):
    _name = "mymodule.mymodel"

    @job
    def my_async_method(self, arg1, arg2):
        """Runs asynchronously in production, synchronously in dev mode."""
        self._do_heavy_work(arg1, arg2)

    def action_trigger(self):
        for record in self:
            record.with_delay().my_async_method("a", "b")
```

## `with_delay()` Options

```python
record.with_delay(
    priority=10,                          # Lower = higher priority (default 10)
    channel="root.mymodule",              # Channel for concurrency control
    description="Processing %s" % record.name,
    max_retries=3,                        # Retries on failure (default 5)
    eta=60,                               # Delay start by N seconds
).my_async_method()
```

## Channel Configuration

Channels control concurrency. Configure in `.env` or `ir.config_parameter`:

```bash
# .env
ODOO_QUEUE_JOB_CHANNELS=root:2,root.whatsapp:1,root.llm:3
```

```
# ir.config_parameter key: queue_job.channels
root:2,root.whatsapp:1,root.llm:3
```

A job's channel defaults to `root`. Use sub-channels to isolate workloads and
prevent one job type from starving others.

## Dev Mode Behavior

```python
# ODOO_DEV_MODE=true  → jobs run SYNCHRONOUSLY (no queue worker needed)
# ODOO_DEV_MODE=false → jobs enqueue and require a worker process
```

In dev mode, `with_delay()` calls the method directly, making testing easy.

## Job Error Handling

```python
from odoo.addons.queue_job.exception import RetryableError

@job
def my_async_method(self):
    try:
        self._do_work()
    except TransientError as e:
        # Re-raise as RetryableError to trigger automatic retry
        raise RetryableError(str(e)) from e
    except Exception as e:
        _logger.error("Job failed permanently: %s", e, exc_info=True)
        # Don't re-raise — job will be marked 'failed', not retried
```

## Checking Job Status

Via Odoo UI: **Technical → Queue Jobs**

```python
# Programmatically
jobs = self.env["queue.job"].search([
    ("model_name", "=", "mymodule.mymodel"),
    ("state", "in", ["pending", "enqueued", "started"]),
])
```

Job states: `pending` → `enqueued` → `started` → `done` / `failed`
