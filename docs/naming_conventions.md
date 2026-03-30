# **Naming Conventions**

This document outlines the naming conventions used for schemas, tables, views, columns, and other objects in the data warehouse.

## **Table of Contents**

1. [General Principles](#general-principles)
2. [Table Naming Conventions](#table-naming-conventions)
   - [Bronze Rules](#bronze-rules)
   - [Silver Rules](#silver-rules)
   - [Gold Rules](#gold-rules)
3. [Column Naming Conventions](#column-naming-conventions)
   - [Surrogate Keys](#surrogate-keys)
   - [Technical Columns](#technical-columns)
4. [Stored Procedure](#stored-procedure-naming-conventions)
---

## **General Principles**

- **Naming Conventions**: Use snake_case, with lowercase letters and underscores (`_`) to separate words.
- **Language**: Use English for all names.
- **Avoid Reserved Words**: Do not use SQL reserved words as object names.

## Principles for Python Code

| Element | Convention | Example |
| --- |------------| --- |
| Entity class | PascalCase | `CustomerOrder` |
| File name | snake_case | `customer_order.py` |
| Variable | snake_case | `customer_order` |
| Function | snake_case | `calculate_total_amount` |
| Database table | snake_case | `customer_order` |
| Database column | snake_case** | `customer_name` |
| Constant | UPPER_CASE | `MAX_RETRIES` |
** These column definitions will be maintained in the silver and gold layer tables; for the bronze layer tables, 
the original column names will be respected.

## **Files Naming Conventions From Entities**
We will consider two types of files for entity naming conventions:

* **Python-based Entity Files:** Files written in Python that represent an entity. An entity is defined as a class or 
object in the code (Object-Oriented Programming) that directly maps to or represents a table in a relational database.
* **DBT SQL Files:** SQL files within the DBT project responsible for transformation processes between the layers of 
the Medallion architecture.


### Python Entity Naming Conventions

All entity class names must include the suffix `_entity`. The following structural rules apply based on the architecture layer:

#### Bronze and Silver Layers: 
- The file and class names must follow the structure: 

- `[Layer Prefix]_<entity>_[Suffix]`

  - `<entity>`: Exact table name from the source system.
  - `[Layer Prefix]`: Exact Layer name for example `silver`, `broze`
  - **Ejemplo:** `bronze_factuas_entity.py`, `silver_clientes_entity`

#### Gold Layer: 
- All names must use meaningful, business-aligned names for tables, starting with the category prefix.
- **`<category>_<entity>`**  
  - `<category>`: Describes the role of the table, such as `dim` (dimension) or `fact` (fact table).  
  - `<entity>`: Descriptive name of the table, aligned with the business domain (e.g., `customers`, `products`, `sales`). This name must be in plural.
  - Examples:
    - `dim_customers` → Dimension table for customer data.  
    - `fact_sales` → Fact table containing sales transactions.  
  


## **Table Naming Conventions**

### **Bronze Rules**
- All names must start with the source system name, and table names must match their original names without renaming.
- **`<sourcesystem>_<entity>`**  
  - `<sourcesystem>`: Name of the source system (e.g., `crm`, `erp`).  
  - `<entity>`: Exact table name from the source system.  
  - Example: `crm_customer_info` → Customer information from the CRM system.

### **Silver Rules**
- All names must start with the source system name, and table names must match their original names without renaming.
- **`<sourcesystem>_<entity>`**  
  - `<sourcesystem>`: Name of the source system (e.g., `crm`, `erp`).  
  - `<entity>`: Exact table name from the source system.  
  - Example: `crm_customer_info` → Customer information from the CRM system.

### **Gold Rules**
- All names must use meaningful, business-aligned names for tables, starting with the category prefix.
- **`<category>_<entity>`**  
  - `<category>`: Describes the role of the table, such as `dim` (dimension) or `fact` (fact table).  
  - `<entity>`: Descriptive name of the table, aligned with the business domain (e.g., `customers`, `products`, `sales`). This name must be in plural.
  - Examples:
    - `dim_customers` → Dimension table for customer data.  
    - `fact_sales` → Fact table containing sales transactions.  

#### **Glossary of Category Patterns**

| Pattern     | Meaning                           | Example(s)                                 |
|-------------|-----------------------------------|--------------------------------------------|
| `dim_`      | Dimension table                  | `dim_clientes`, `dim_articulos`            |
| `fact_`     | Fact table                       | `fact_sales`                               |
| `report_`   | Report table                     | `report_customers`, `report_sales_monthly` |

## **Column Naming Conventions**

### **Auxiliary Columns**
Columns created **only during the transformation process in dbt** to support intermediate calculations, parsing, validations, or business rule implementations.

These columns **must not exist in the final model** and are intended solely for use within **CTEs or intermediate transformation steps**. 

They are considered **technical columns used during data processing** and **do not represent business attributes**.

- **`aux_<description>`**
  - `aux_`: A prefix indicating that this column is an **auxiliary transformation column**.
  - `<description>`: A short, descriptive name explaining the transformation purpose of the column.

- **Rules:**
  - Must be used **only within intermediate transformations (CTEs, staging logic, or transformation steps)**.
  - Must **not appear in the final SELECT** of the model.
  - Should have **a single clear transformation purpose** (parsing, classification, flags, or temporary calculations).
  - Must be **removed before the final dataset is materialized**.

- **Examples:**
  - `aux_vigencia_plan` → Temporary column used to extract the validity period from a product description.
  - `aux_tipo_plan` → Auxiliary column used to classify plan types based on business rules.
  - `aux_flag_facturacion` → Temporary flag used during transformation to identify billing-related records.

### **Surrogate Keys**  
All primary keys in dimension tables must use the prefix `id_`.
- **`id_<entity>`**
  - `id_`: A prefix indicating that this column is a surrogate key.  
  - `<entity>`: Descriptive name of the table, aligned with the business domain (e.g., `customers`, `products`, `sales`). This name must be in plural.  
  
  - Example: `id_clientes` → Surrogate key in the `dim_clientes` table.
  
### **Technical Columns**
All technical columns must start with the prefix `dwh_`, followed by a descriptive name indicating the column's purpose.
- **`dwh_<column_name>`**  
  - `dwh`: Prefix exclusively for system-generated metadata.  
  - `<column_name>`: Descriptive name indicating the column's purpose.  
  - Example: `dwh_load_date` → System-generated column used to store the date when the record was loaded.
 
## **Stored Procedure**

- All stored procedures used for loading data must follow the naming pattern:
- **`load_<layer>`**.
  
  - `<layer>`: Represents the layer being loaded, such as `bronze`, `silver`, or `gold`.
  - Example: 
    - `load_bronze` → Stored procedure for loading data into the Bronze layer.
    - `load_silver` → Stored procedure for loading data into the Silver layer.
