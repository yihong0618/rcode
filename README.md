## Rcode

This repo is fork from [code-connect](https://github.com/chvolkmann/code-connect)
Thanks for this cool repo.

https://user-images.githubusercontent.com/1651790/172983742-b27a3fe0-2704-4fc8-b075-a6544783443a.mp4


## What changed

1. PyPI
2. support local open remote dir command `rcode ${ssh_name} ${ssh_dir}`
3. support cursor to open remote dir command `rcursor ${ssh_name} ${ssh_dir}`
4. you can also open dir from remote to local `cursor` just `cursor ${dir_name}`

## INFO

1. pip3 install rcode (or clone it pip3 install .)
2. install socat like: (sudo yum install socat)
3. just `rcode file` like your VSCode `code .`
4. or use cursor just `cursor .`
5. local open remote use rcode if you use `.ssh/config` --> `rcode remote_ssh ~/test`
6. local open latest remote `.ssh/config` --> `rcode -l or rcode --latest`
7. add shortcut_name `rcode s ~/abc -sn abc` then you can use `rcode -os abc` to open this dir quickly
8. support cursor to open remote dir command `rcursor ${ssh_name} ${ssh_dir}`

> Note:
> - Be sure to [connect to the remote host](https://code.visualstudio.com/docs/remote/ssh#_connect-to-a-remote-host) first before typing any `rcode` in the terminal
> - We may want to add `~/.local/bin` in to your `$PATH` in your `~/.zshrc` or `~/.bashrc` to enable `rcode` being resolved properly
> ```diff
> - export PATH=$PATH:/usr/local/go/bin
> + export PATH=$PATH:/usr/local/go/bin:~/.local/bin
> ```
