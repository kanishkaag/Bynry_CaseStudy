from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.json or {}

    # 1. Required field validation
    required_fields = ['name', 'sku', 'price', 'warehouse_id']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

    # 2. Input type & constraint validation
    try:
        price = float(data['price'])
        if price <= 0:
            return jsonify({"error": "Price must be positive"}), 400

        quantity = int(data.get('initial_quantity', 0))
        if quantity < 0:
            return jsonify({"error": "Quantity cannot be negative"}), 400

        sku = str(data['sku']).strip()
        if not sku:
            return jsonify({"error": "SKU cannot be empty"}), 400

    except (ValueError, TypeError):
        return jsonify({"error": "Invalid input types"}), 400

    try:
        # 3. Warehouse validation
        warehouse = Warehouse.query.get(data['warehouse_id'])
        if not warehouse:
            return jsonify({"error": "Invalid warehouse_id"}), 400

        # (Optional: add company ownership check if available)
        # if warehouse.company_id != current_user.company_id:
        #     return jsonify({"error": "Unauthorized warehouse access"}), 403

        # 4. Idempotency / duplicate SKU prevention
        existing_product = Product.query.filter_by(sku=sku).first()
        if existing_product:
            return jsonify({"error": "SKU already exists"}), 409

        # 5. Create product (decoupled from warehouse)
        product = Product(
            name=data['name'],
            sku=sku,
            price=price
        )
        db.session.add(product)
        db.session.flush()  # ensures product.id is available

        # 6. Create inventory record
        inventory = Inventory(
            product_id=product.id,
            warehouse_id=warehouse.id,
            quantity=quantity
        )
        db.session.add(inventory)

        # 7. Atomic commit
        db.session.commit()

        return jsonify({
            "message": "Product created successfully",
            "product_id": product.id
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Duplicate SKU detected"}), 409

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error"}), 500