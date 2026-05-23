# Installation

## 1. Install the AVL binary

AVL is a Fortran program distributed as source by MIT. Build it and place the binary at `~/bin/avl`.

``````{tab-set}

`````{tab-item} macOS
:sync: macos

1. Install dependencies and create a plain `gfortran` symlink:

   ```bash
   brew install --cask xquartz
   brew install gcc
   mkdir -p ~/bin
   ln -sf "$(ls /opt/homebrew/bin/gfortran-* | head -1)" ~/bin/gfortran
   export PATH="$HOME/bin:$PATH"  # add to ~/.zshrc
   ```

2. Download the latest AVL source tarball (`*.tgz`) from <https://web.mit.edu/drela/Public/web/avl/> and extract it:

   ```bash
   tar -xzf ~/Downloads/avl*.tgz -C ~/Downloads
   ```

   This creates:

   ```{code-block} text
   :class: no-copybutton filetree
   📁 ~/Downloads/AVL<version>/
   ├── 📁 eispack/
   ├── 📁 plotlib/
   └── 📁 bin/
   ```

3. Build each component and install the binary:

   ```bash
   cd ~/Downloads/AVL*/eispack
   make -f Makefile.gfortran FC=gfortran
   cd ../plotlib
   cp config.make.gfortranDP config.make
   make gfortranDP FC=gfortran CC=/usr/bin/cc
   cd ../bin
   make -f Makefile.gfortranDP FC=gfortran
   cp avl ~/bin/avl
   ```

`````

`````{tab-item} Linux
:sync: linux

1. Install dependencies and create `~/bin`:

   ```bash
   sudo apt install gfortran libx11-dev   # Debian/Ubuntu
   # sudo dnf install gcc-gfortran libX11-devel  # Fedora/RHEL
   mkdir -p ~/bin
   ```

2. Download the latest AVL source tarball (`*.tgz`) from <https://web.mit.edu/drela/Public/web/avl/> and extract it:

   ```bash
   tar -xzf ~/Downloads/avl*.tgz -C ~/Downloads
   ```

   This creates:

   ```{code-block} text
   :class: no-copybutton filetree
   📁 ~/Downloads/AVL<version>/
   ├── 📁 eispack/
   ├── 📁 plotlib/
   └── 📁 bin/
   ```

3. Build each component and install the binary:

   ```bash
   cd ~/Downloads/AVL*/eispack
   make -f Makefile.gfortran FC=gfortran
   cd ../plotlib
   cp config.make.gfortranDP config.make
   make gfortranDP FC=gfortran CC=/usr/bin/cc
   cd ../bin
   make -f Makefile.gfortranDP FC=gfortran
   cp avl ~/bin/avl
   ```

`````

`````{tab-item} Windows
:sync: windows

1. Download the pre-built `avl.exe` from the [AVL download page](https://web.mit.edu/drela/Public/web/avl/).

2. Create a folder for the binary and move `avl.exe` into it:

   ```powershell
   mkdir "$HOME\AppData\Local\Programs\avl"
   move "$HOME\Downloads\avl*.exe" "$HOME\AppData\Local\Programs\avl\avl.exe"
   ```

3. Add that folder to your PATH permanently:

   ```powershell
   [Environment]::SetEnvironmentVariable(
       "PATH",
       "$HOME\AppData\Local\Programs\avl;" + [Environment]::GetEnvironmentVariable("PATH", "User"),
       "User"
   )
   ```

   Close and reopen any terminals for the change to take effect. You can also do this through **System Settings → System → About → Advanced system settings → Environment Variables** — edit the `Path` entry under *User variables* and append `%USERPROFILE%\AppData\Local\Programs\avl`.

```{note}
On Windows, `avl-aero-tables verify` locates `avl.exe` via PATH — not `~/bin/avl`. As long as the folder above is on your PATH, the verify step below will succeed.
```

`````

``````

### Verify

```bash
avl-aero-tables verify
# AVL x.xx found at /Users/you/bin/avl — OK
```

```{tip}
Run `avl-aero-tables verify` after any system update or PATH change to confirm the binary is still reachable.
```

## 2. Install the Python package

Requires Python 3.12 or later:

```bash
python3 --version
# Python 3.12.x or later required
```

```bash
python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

pip install avl-aero-tables
```
