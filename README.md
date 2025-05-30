# NetworkPuzzles

NetworkPuzzles is a simple program for teaching network principles. It was inspired by watching a number of people struggling with PacketTracer in an attempt to undestand IP addresses, subnets, and gateways. Most of their struggles were with understanding how to configure an IP on each device; they never got around to learning about how the subnets worked.

NetworkPuzzles is geared to take all the complexity away, and let you visualize the network and packet flow in a very simple way. It has proven itself already, as a great tool for teaching in lab-settings in Africa.

It is also set up to be a tool for self-teaching; If you can solve all the built-in puzzles, you should be well on your way to mastering networking.

## Development

Ensure Python >=3.12 is installed and in `$PATH`.

Clone the repository and enter into the root folder; e.g.
```shell
git clone https://github.com/tyounglightsys/NetworkPuzzles.git
cd NetworkPuzzles
```

Create a virtual environment and activate it; e.g.
```shell
python -m venv env
. env/bin/activate      # bash terminal; OR
./env/bin/Activate.ps1  # powershell terminal
```

Install python dependencies [by installing python package].
```shell
python -m pip install .         # for regular development; OR
python -m pip install .[build]  # to include build tools (generally not needed)
```

Run the CLI app:
```shell
python -m src.network_puzzles
```

Run the GUI app:
```shell
python src/main.py
```

Run python unittests (simple output):
```
(env) ~/NetworkPuzzles$ ./scripts/run-tests.sh
....ss........................
----------------------------------------------------------------------
Ran 30 tests in 0.054s

OK (skipped=2)
```

Run python unittests (verbose output):
```
(env) ~/NetworkPuzzles$ ./scripts/run-tests.sh -v
[...]
test_linkfromname_found (tests.test_puzzle.TestXFromY.test_linkfromname_found) ... Loaded: Level0-HubVsSwitch
ok
test_linkfromname_notfound (tests.test_puzzle.TestXFromY.test_linkfromname_notfound) ... Loaded: Level0-HubVsSwitch
ok
test_nicfromid_found (tests.test_puzzle.TestXFromY.test_nicfromid_found) ... Loaded: Level0-HubVsSwitch
ok
test_nicfromid_notfound (tests.test_puzzle.TestXFromY.test_nicfromid_notfound) ... Loaded: Level0-HubVsSwitch
ok
test_nicfromname_found (tests.test_puzzle.TestXFromY.test_nicfromname_found) ... Loaded: Level0-HubVsSwitch
ok
test_nicfromname_notfound (tests.test_puzzle.TestXFromY.test_nicfromname_notfound) ... Loaded: Level0-HubVsSwitch
ok

----------------------------------------------------------------------
Ran 30 tests in 0.049s

OK (skipped=2)
```


## Prerequisites

Ubuntu (more specifically Wayland) requires the installation of the `xsel`
package for selection and clipboard features to work (Kivy runs under XWayland).