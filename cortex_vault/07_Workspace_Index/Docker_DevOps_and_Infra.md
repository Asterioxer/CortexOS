---
title: "Docker, DevOps & Distributed Big Data Infrastructure Workspace"
type: "workspace_catalog"
tags:
  - cortex/workspaces
  - cortex/docker
  - cortex/hadoop
  - cortex/spark
  - cortex/jenkins
  - cortex/devops
last_updated: "2026-10-27"
status: "verified"
---

# 🐳 Docker, DevOps & Distributed Big Data Infrastructure Workspace

- **Location**: `C:\Users\soham\Desktop\Docker`
- **Domain**: Containerization, Distributed Data Processing (Hadoop / Spark / Hive), CI/CD Automation (Jenkins), Agile DevOps
- **Primary Toolchains**: Docker 29.4.3, Docker Compose, Docker Swarm, Jenkins, Apache Hadoop, Apache Spark, Apache Hive, Bash / Make

## 🏛️ Infrastructure Stacks & Repositories

### 1. Hadoop & Spark Workbench (`docker-hadoop-spark-workbench/`)
A distributed big data cluster packaged as multi-container Docker Compose and Docker Swarm environments:
- **Core Services**:
  - `namenode` & `datanode`: Hadoop Distributed File System (HDFS) master and worker daemons.
  - `resourcemanager` & `nodemanager`: YARN cluster scheduling and node resource allocation.
  - `spark-master` & `spark-worker`: Distributed Apache Spark in-memory compute cluster.
  - `hive-server` & `hive-metastore`: Distributed SQL query engine over HDFS data lakes with PostgreSQL / MySQL metastore.
- **Automation Scripts**:
  - `start-hadoop-spark-workbench.sh`: Spawns base HDFS + Spark nodes.
  - `start-hadoop-spark-workbench-with-Hive.sh`: Spawns full stack including Hive SQL metastore and Thrift server.
  - `scale-up-spark-worker.sh`: Dynamically scales Spark worker containers (`docker compose up --scale spark-worker=N`).
  - `swarm/`: Production Docker Swarm overlay network configurations for multi-host deployments.

---

### 2. Jenkins CI/CD Automation Pipeline (`Devops/jenkins-docker-installation/`)
- **Docker-in-Docker (DinD)**: Jenkins controller container mounting the host Docker daemon socket (`/var/run/docker.sock`) to build, test, and package application containers natively.
- **Pipeline as Code**: `Jenkins-Demo-Projects/Jenkinsfile` defining declarative multi-stage build, lint, test, and artifact publishing pipelines.
- **Academic / Industry Context**: Accompanied by comprehensive curriculum materials (`Stream 1 _  Agile and DevOps (1).pptx`).

---

## ⚡ Interaction with CortexOS
CortexOS's local somatosensory agent monitors Docker engine health via the Docker CLI (`docker ps`, `docker stats`) when background containers are active, ensuring memory allocation remains within host limits (24 GB RAM, 4GB VRAM).

---
## Related Notes
- [[07_Workspace_Index/Desktop_Workspace_Master_Index|Desktop Workspace Master Index]]
- [[05_System_State/Toolchains_and_Compilers|Toolchains and Compilers]]
- [[05_System_State/Filesystem_and_Workspaces|Filesystem and Workspaces]]
- [[01_Architecture/Autonomous_Daemons|Autonomous Supervisors and Daemons]]
