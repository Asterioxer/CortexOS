---
title: "Spring Boot 3 E-Commerce Suite & Java Enterprise Workspace"
type: "workspace_catalog"
tags:
  - cortex/workspaces
  - cortex/springboot
  - cortex/java
  - cortex/jpa
  - cortex/react
last_updated: "2026-10-27"
status: "verified"
---

# ☕ Spring Boot 3 E-Commerce Suite & Java Enterprise Workspace

- **Location**: `C:\Users\soham\Desktop\SpringBoot`
- **Domain**: Enterprise Java Microservices, Spring Data JPA, RESTful API Design, React Full-Stack Integration
- **Primary Toolchains**: Java 21 LTS (`java 21.0.9`), Apache Maven (`mvnw`), Spring Boot 3.5+, Vite, React, Axios, H2 / PostgreSQL

## 🏢 Projects & Modules Overview

| Project Directory | Architecture & Tech Stack | Description & Components |
|---|---|---|
| **`ecom-proj`** | Spring Boot 3.5.7 + Java 21 + Spring Data JPA + H2 / Postgres | Full enterprise e-commerce backend. Exposes REST endpoints for product catalog, inventory status, shopping cart, and orders. |
| **`ecom-frontend-1`** | React 18 + Vite + Axios | Single-page client frontend communicating with `ecom-proj` REST endpoints (`axios.jsx`), featuring product listing, search filters, and checkout cart. |
| **`MyDIApp`** | Spring Framework Core | Lab project illustrating Dependency Injection (DI), Inversion of Control (IoC) containers, `@Component`, `@Autowired`, and Bean lifecycles. |
| **`DemoWithoutSpring`** | Pure Java SE (Maven) | Contrast benchmark demonstrating tight coupling and manual instantiation without IoC containers. |
| **`simpleWebApp`** | Spring Boot Web Starter | Lightweight web starter testing Spring MVC controllers and JSON serialization. |
| **`DemoApp`** | Spring Boot Core | Hello-world service validation and Maven wrapper testing. |

---

## 🛠️ Build & Development Lifecycle
- **Backend Build & Run**:
  ```powershell
  cd "C:\Users\soham\Desktop\SpringBoot\ecom-proj"
  .\mvnw.cmd clean spring-boot:run
  ```
  Runs embedded Tomcat server on port `8080`, with H2 in-memory console available at `http://localhost:8080/h2-console`.
- **Frontend Build & Run**:
  ```powershell
  cd "C:\Users\soham\Desktop\SpringBoot\ecom-frontend-1"
  npm install
  npm run dev
  ```
  Spawns Vite hot-reloading dev server on port `5173`.

---

## 🔗 Pair Copilot Integration
CortexOS can inspect `ecom-proj` pom configurations, diagnose Java compile errors, and launch the dev servers via [[02_Pair_Programming/Pair_Programming_Copilot|Pair Copilot]].

---
## Related Notes
- [[07_Workspace_Index/Desktop_Workspace_Master_Index|Desktop Workspace Master Index]]
- [[05_System_State/Toolchains_and_Compilers|Toolchains and Compilers]]
- [[05_System_State/Filesystem_and_Workspaces|Filesystem and Workspaces]]
