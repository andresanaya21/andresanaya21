---

## ✅ **Prerequisites**

* Ubuntu 20.04 / 22.04 (both are fine)
* Git
* GCC / g++
* CMake
* asio
* libyaml-cpp-dev
* make

---

## 🔹 **Step 1: Install Required Packages**

Open a terminal and run:

```bash
sudo apt update
sudo apt install git build-essential cmake libsctp-dev lksctp-tools \
    libyaml-cpp-dev
```

*(Note: `libsctp-dev` and `lksctp-tools` are important for SCTP support)*

If your Ubuntu doesn’t have **asio** installed:

```bash
sudo apt install libasio-dev
```

If not available in your version’s repo, UERANSIM will use **standalone Asio** during build (so you can skip it).

---

## 🔹 **Step 2: Clone UERANSIM Source Code**

```bash
git clone https://github.com/aligungr/UERANSIM.git
cd UERANSIM
```

By default, it will clone the latest version. If you want a specific version:

```bash
git checkout v3.2.6   # Example version
```

---

## 🔹 **Step 3: Build UERANSIM**

```bash
make
```

This will compile both the **gNB** and **UE** binaries:

* `nr-gnb`
* `nr-ue`

You should now see these binaries inside the folder.

---

## 🔹 **Step 4: Run UERANSIM**

Example:

```bash
./build/nr-gnb -c config/open5gs-gnb-cilium.yaml
./build/nr-ue -c config/open5gs-ue-cilium.yaml
```

*(Replace with your own configuration files)*

---

## 🔍 **Verify SCTP Modules**

Make sure SCTP is enabled in your kernel:

```bash
lsmod | grep sctp
```

If it’s empty:

```bash
sudo modprobe sctp
```

And to load it permanently:

```bash
echo "sctp" | sudo tee -a /etc/modules
```

---

## ✅ Summary

| Step | Action                            |
| ---- | --------------------------------- |
| 1    | Install build tools and libraries |
| 2    | Clone UERANSIM repo               |
| 3    | Build with `make`                 |
| 4    | Configure and run gNB/UE          |

---
