# Build

Requires multiplatform build. Macos has QEMU installed already, you may need to set up QEMU yourself on other systems.
```bash
uv build
docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/dsikkema/playdo:latest -t ghcr.io/dsikkema/playdo:<latest version number> --push .
```

# Install database

Must copy install.sh and schema.sql from the repo to install a new DB, or else use an existing DB.
```bash
PLAYDO_DATABASE_PATH=data/playdo.db ./install.sh
```

# Run
Need a `.docker.env` file with the following variables:
```
PLAYDO_DATABASE_PATH=/app/data/playdo.db # path inside the container
PLAYDO_DEBUG=true
PLAYDO_ANTHROPIC_MODEL=claude-3-haiku-20240307
PLAYDO_TESTING=false
ANTHROPIC_API_KEY=etc
PLAYDO_JWT_SECRET_KEY=something_very_secure_and_random
```

And run the container:
```bash
docker run --name my_playdo_backend -d -p 5000:5000  --env-file .docker.env -v  $(pwd)/data:/app/data ghcr.io/dsikkema/playdo:latest
```

Once container is running, you can exec into it to use CLI tools:
```bash
docker exec -it my_playdo_backend /bin/bash
# inside container
playdo-users list
playdo-cli
```


