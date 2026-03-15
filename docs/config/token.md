# Token

!!! important "Securely storing authentication tokens"
    You should not put authentication tokens as plain text into anything that might be
    accessed from elsewhere. This includes git repos.
    If you want to store tokens securely you can use something like a secrets vault,
    which most cloud providers (AWS, Azure, GCP) and git hosting systems (e.g. GitHub)
    provide in order to keep secrets secure and only inject them at run time.

## Creating a bot and inviting it into the server

### Creating the bot and getting a token

In order to generate a token you need to:

- Go to the [Discord Developer Applications Portal](https://discord.com/developers/applications)
- Create an application using the `New Application` button at the top right
- Set up your bot with a name on the `General Information` page, and ideally choose an
appropriate picture for your bot
- In the description of the bot add the required description set out in the licence:
  > Original code by Baddadan/Kashual for NoP EU. GitHub: https://bit.ly/3ZrVj7C
  > Discord-LFG by dukes for NoP EU. https://github.com/aptosaurinae/discord-lfg
- Under `Installation` in the `Install Link` drop down select `None`
- On the `Bot` page:
    - Turn off `Public Bot` and then save changes
    - Click `Reset Token` to generate a new token.
    - Copy the token and store it somewhere securely where you want to use it, such as a
    GitHub or cloud secrets vault.

### Inviting the bot to your server

- On the `OAuth2` page:
    - scroll down to `OAuth2 URL Generator` and select `bot` from the
    permissions list, and make sure `Integration Type` is set to `Guild`.
    You should not need to select any sub-permissions from the `bot` list, as you can then
    configure the permissions the bot has access to via role assignment within the server.
    - Click the `copy` button at the right of the `Generated URL` field and put it in your browser.
    - This should either directly give you an invite page where you can select a discord server,
    or load up your discord desktop client and allow you to choose there.
- Once the bot is in your server you can then apply roles so that it can access channels
to listen for commands.
