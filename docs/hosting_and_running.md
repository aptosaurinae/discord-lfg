# Hosting

If you want to host the bot locally for testing (or temporarily / on a local machine) you can either directly use the GitHub repo, or use a docker image from docker-hub, and you can do these either locally or on a remote machine.

## Using the GitHub repo

- Create the required configs, including [getting a token](config/token.md)
- Follow the [installation instructions](installation.md)

--8<-- "README.md:docs-running"

## Using Docker

- Get Docker Desktop
- Follow the Docker setup to be able to run Docker (in Windows via WSL)
- run `docker pull aptosaurinae/discord-lfg` to get the latest image
- Make sure the files are accessible in the shell - if you're using WSL this might mean needing to use the `/mnt` folder.
- Run the docker image. The following command assumes config files have been copied into the `/etc/discord-lfg/` directory and folders have been created for stats and logging. the file paths used in the right side of each volume element need to match those listed in the config file e.g. `log_folder` in the config needs to point at `/config/logging`.

``` shell
docker run -d --user root\
  -v /etc/discord-lfg/discord-bot-test-token:/secrets/discord-bot-token:ro \
  -v /etc/discord-lfg:/config:ro \
  -v /etc/discord-lfg/logging:/config/logging:rw \
  -v /etc/discord-lfg/stats-test:/config/stats:rw \
  aptosaurinae/discord-lfg:latest \
  --token /secrets/discord-bot-token \
  --config /config/discord-lfg-test-config-docker.toml
```

The `-d` flag will leave the docker container running in the background. If you want to see the log output in the console (useful when testing), remove this flag.

## Hosting on a Google Cloud Virtual Machine

***(alternative hosting options are available)***

### Creating a VM

- Make sure you have all of the config info to hand for the bot.
- Create an account and log in.
- Create a new project.
- Once the new project loads, click on `Create a VM` which should take you to the Google Compute VM creation page. If it asks you to enable GCE then do so, wait a moment, and try again.
- In the machine config, rename the instance at the top, then point it at a local region, and select an appropriate instance size (I'd recommend something like an E2-small).
- Click "Create". this might fail if it can't find the selected machine size in the given region, so you may need to try again with a different region.
- Once created, you can access the VM by clicking the "SSH" button under "Connect". This will start up a shell giving you access to the VM.

### Setting up the VM

- Reboot the VM (exit the shell, stop it and start it again, reopen the shell)
- Either upload your config files using the tool on the shell browser window, or copy the files in from a bucket.
- Follow either of the GitHub or Docker instructions above. If you are following the Docker instructions, you'll need to run the Linux command line install instructions from [here](https://docs.docker.com/engine/install/) instead of using Docker Desktop.

## Command preview within Discord

Once the bot is up and running, the commands that are active should match those defined in
the command files referenced by the main config, along with the two default `lfghistory` and
`lfgstats` commands.

![Commands preview within Discord](img/lfg_commands_preview.png)
