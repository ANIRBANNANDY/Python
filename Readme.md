Here is the concise requirement summary for your Multi-Server Monitoring Dashboard system.

### **1. Infrastructure & Connectivity**

* **Architecture:** A **Hub-and-Spoke** model. One central "Hub" (Server 1) serves the UI, communicating with "Agents" (Servers 1–6).
* **Dynamic Identity:** The Hub accepts its hostname (e.g., `server.xyz.com`) via command-line arguments for UI display.
* **Networking:** All scripts run on `0.0.0.0` to listen across all network interfaces.
* **Persistence:** Background execution via Batch scripts and Windows Task Scheduler (At Startup/Logon) to ensure "always-on" availability.

### **2. Process Management (Kill Logic)**

* **Global Cleanup:** Targeted termination of **any** `perl.exe` process containing the string "xyz" in its command line.
* **SAS Termination:** Immediate follow-up termination of **all** `sas.exe` processes regardless of user.
* **Reliability:** A recursive 3-cycle loop with 5-second delays to ensure Windows releases file locks before attempting file deletion.

### **3. Security & Authentication**

* **Active Directory (AD) ACL:** Access to the Hub is restricted to members of two specific AD groups (e.g., `APP_Monitor_Users`, `APP_Monitor_Admins`).
* **Identity Source:** AD group verification is managed at the Hub layer via LDAP or Windows Token evaluation.
* **Execution Context:** Front-end users are authenticated for viewing; all back-end file/process actions are executed by a **Service (SVC) Account**.

### **4. User Interface Features**

* **Time Management:** Live digital clocks for **IST (India)** and **CET (Europe)** with the current date.
* **Queue Manager:** A real-time file list of the Queue folder, including a **Total File Count** badge in the header.
* **Health Monitoring:** Dedicated **Disk Health** panel showing % used, total, and free space for **C:** and **D:** drives for the selected server.
* **Server Explorer:** Navigation tree to browse, view logs, and delete folders within the project directories.

### **5. Configuration Management**

* **Centralized Config:** All variable settings (IP lists, ports, AD group names, folder paths) are stored in a single `config.json` file.
* **Dynamic Access:** The Hub provides a `/get-config` endpoint to keep the front-end synchronized with back-end settings.

---

**Would you like me to create a "Deployment Checklist" to ensure all 6 servers are configured identically before you go live?**
