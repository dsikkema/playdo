FROM python:3.12-slim

WORKDIR /app

# Copy just the wheel file
COPY dist/playdo-0.1.0-py3-none-any.whl /app/

# Install the wheel (which installs dependencies too)
RUN pip install playdo-0.1.0-py3-none-any.whl

# Expose the port your Flask app runs on
EXPOSE 5000

# This is where we need to define how to run your application
# The command depends on how your app is structured
CMD ["python", "-m", "playdo.app"]
