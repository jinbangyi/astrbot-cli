- [x] create a command, user can quick start an astrbot
  - start astrbot from code source
    0. use `cwd`/data/astrbot as the working directory
    1. check the dependencies: python3, uv, node, pnpm, pm2 if not exist, prompt user to install
    2. clone the repo: `https://github.com/AstrBotDevs/AstrBot.git`, and cd into the repo
    3. build from codesource
      - init python env
        1. create a virtual environment: `uv venv`
        2. install dependencies: `uv sync`
      - init dashboard env(node)
        1. cd into dashboard: `cd dashboard`
        2. install dependencies: `pnpm install`
        3. build dashboard: `pnpm run build`
    4. use pm2 to start astrbot: `python main.py --webui-dir dashboard/dist`

  - the command i mean is to create a command line, in python use tyro
- [ ] create a command, user can install/uninstall/update/list/config plugins
