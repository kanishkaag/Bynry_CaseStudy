-- Companies
CREATE TABLE Company (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Warehouses
CREATE TABLE Warehouse (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES Company(id)
);

-- Products
CREATE TABLE Product (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) NOT NULL UNIQUE,
    price DECIMAL(10,2) NOT NULL CHECK (price > 0),
    product_type VARCHAR(50) DEFAULT 'simple', -- simple / bundle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES Company(id)
);

-- Inventory (Product per Warehouse)
CREATE TABLE Inventory (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity >= 0),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES Product(id),
    FOREIGN KEY (warehouse_id) REFERENCES Warehouse(id),
    UNIQUE (product_id, warehouse_id)
);

-- Inventory Change Log
CREATE TABLE InventoryLog (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    change INT NOT NULL,
    reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES Product(id),
    FOREIGN KEY (warehouse_id) REFERENCES Warehouse(id)
);

-- Suppliers
CREATE TABLE Supplier (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product-Supplier Mapping (Many-to-Many)
CREATE TABLE ProductSupplier (
    product_id INT NOT NULL,
    supplier_id INT NOT NULL,
    PRIMARY KEY (product_id, supplier_id),
    FOREIGN KEY (product_id) REFERENCES Product(id),
    FOREIGN KEY (supplier_id) REFERENCES Supplier(id)
);

-- Product Bundles (Composite Products)
CREATE TABLE ProductBundle (
    bundle_id INT NOT NULL,
    child_product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (bundle_id, child_product_id),
    FOREIGN KEY (bundle_id) REFERENCES Product(id),
    FOREIGN KEY (child_product_id) REFERENCES Product(id)
);