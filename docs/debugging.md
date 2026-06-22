# Debugging Guide for Developers

This guide helps developers troubleshoot common issues while working on The Inventory project. It covers debugging techniques, useful tools, API debugging, database issues, authentication problems, cache issues, and performance profiling.

 ## Quick Debugging Checklist

Before debugging deeply, check the basics first:

1. Make sure dependencies are installed.
2. Confirm environment variables are correctly configured.
3. Verify the database is running and migrations are applied.
4. Check the server logs for error messages.
5. Reproduce the issue with clear steps.
6. Identify whether the issue is related to API, database, authentication, cache, or frontend behavior.
7. Test one change at a time.

 ## Debugging Techniques

 ### Using Django Debug Toolbar

Django Debug Toolbar helps developers inspect requests, SQL queries, cache usage, templates, and timing information while debugging locally.

To use it during development:

1. Install the package if it is not already available:

```bash
pip install django-debug-toolbar
```

2. Add `debug_toolbar` to `INSTALLED_APPS` in the development settings.
3. Add the debug toolbar middleware near the top of `MIDDLEWARE`.
4. Include the debug toolbar URLs in the development URL configuration.
5. Run the development server and open the application in the browser.

Use the toolbar to inspect:

- SQL queries and duplicate queries
- Request and response details
- Cache usage
- Template rendering
- Request timing and performance issues

Do not enable Django Debug Toolbar in production.

1. Using Logging

Logging helps track application behavior without stopping execution.

Example:

    import logging

    logger = logging.getLogger(__name__)

    def get_products():
        logger.info("Fetching products from the database")
        try:
            # product query logic
            logger.info("Products fetched successfully")
        except Exception as exc:
            logger.error("Failed to fetch products: %s", exc)
            raise

Use logging when you want to inspect runtime behavior, request data, database results, or unexpected errors.

2. Using Breakpoints

Breakpoints allow developers to pause code execution and inspect variables.

Use breakpoints when:

- A variable has an unexpected value
- A function is not behaving as expected
- You need to follow the execution flow step by step

In VS Code, click near the line number to add a breakpoint, then run the debugger.

3. Using pdb Debugger

The Python "pdb" debugger helps inspect code directly from the terminal.

Example:

import pdb

def calculate_total(items):
    pdb.set_trace()
    total = sum(item.price for item in items)
    return total

Useful commands:

n    # next line
s    # step into function
c    # continue execution
p variable_name    # print variable value
q    # quit debugger

4. Using Django Shell

Django shell is useful for testing models, queries, and utility functions.

Run:

    cd src
    python manage.py shell
Example:

from inventory.models import Product

products = Product.objects.all()
print(products.count())


Use Django shell to verify database records, test queries, and inspect model behavior.

## Debugging API Endpoints

When an API endpoint fails, follow these steps:

1. Confirm the endpoint URL is correct.
2. Check the HTTP method such as GET, POST, PUT, PATCH, or DELETE.
3. Verify request headers.
4. Validate request body or query parameters.
5. Check authentication tokens or cookies.
6. Inspect the response status code and error message.
7. Review backend logs.

Example using curl:

curl -X GET http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer your_access_token"

Example POST request:

curl -X POST http://localhost:8000/api/v1/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_access_token" \
  -d '{"name": "Sample Product", "price": 100}'

Common API status codes:

 | Status Code | Meaning | Common Cause |
 |------------|---------|--------------|
 | 400 | Bad Request | Invalid request data |
 | 401 | Unauthorized | Missing or invalid token |
 | 403 | Forbidden | User does not have permission |
 | 404 | Not Found | Resource or endpoint does not exist |
 | 500 | Server Error | Unhandled backend error |

## Debugging Database Issues

Common database issues include missing migrations, incorrect queries, connection failures, and invalid data.

Check migrations

     cd src
     python manage.py showmigrations
     python manage.py migrate --plan
     python manage.py migrate

Inspect database queries

Use Django shell:

from src.api.models import Product

Product.objects.filter(is_active=True)

Common database problems

 | Problem | Possible Solution |
 |---------|-------------------|
 | Migration error | Run migrations again and check model changes |
 | Table does not exist | Confirm migrations were applied |
 | Empty query result | Check filters and test data |
 | Slow query | Add indexes or optimize filters |
 | Connection error | Check database settings and environment variables |

## Debugging Authentication Issues

Authentication issues usually happen because of missing tokens, expired tokens, invalid cookies, or incorrect headers.

Steps to debug:

1. Check whether the access token exists.
2. Confirm the token is sent in the correct header.
3. Verify cookie-based authentication if used.
4. Check token expiry.
5. Confirm the user has the required permissions.

Example Authorization header:

Authorization: Bearer your_access_token

Common authentication errors:

 | Error | Possible Cause | Fix |
 |-------|----------------|-----|
 | Invalid token | Token expired or malformed | Generate a new token |
 | Authentication credentials were not provided | Missing header or cookie | Send valid credentials |
 | Permission denied | User lacks required role | Check user permissions |

## Debugging Cache Issues

Cache issues can cause stale or outdated data.

Steps to debug cache problems:

1. Clear the cache.
2. Confirm cache keys are unique.
3. Check whether cached data is being invalidated correctly.
4. Compare cached response with fresh database response.

Example:

    from django.core.cache import cache

    cache.clear()

## Performance Profiling

Performance profiling helps identify slow code, expensive queries, and memory issues.

### Measure execution time

    import time

    start = time.perf_counter()

    # code to measure

    end = time.perf_counter()
    print(f"Execution time: {end - start} seconds")

### Query optimization tips

- Avoid unnecessary database queries.
- Use "select_related()" for foreign key relationships.
- Use "prefetch_related()" for many-to-many relationships.
- Add indexes for frequently filtered fields.
- Paginate large API responses.

Example:

```python
from inventory.models import Product

products = Product.objects.select_related("category").filter(is_active=True)
```

## Troubleshooting Flowchart

```text
Issue occurs
    |
    v
Can you reproduce it?
    |
    +-- No --> Collect logs, request details, and document the steps.
    |
    +-- Yes --> Identify the affected layer.
                    |
                    v
          API / Database / Authentication / Cache / Performance
                    |
                    v
          Run the relevant debugging tool or command.
                    |
                    v
          Fix the issue, add tests if needed, and verify again.
```

## Best Practices

- Read the full error message before changing code.
- Reproduce the issue consistently.
- Debug one problem at a time.
- Use logs instead of random print statements in production code.
- Keep error messages clear and actionable.
- Add tests when fixing bugs.
- Document repeated issues for future developers.

## Related Files

- "docs/troubleshooting.md"
- "docs/api.md"
- "src/the_inventory/settings/base.py"
- "src/api/middleware.py"