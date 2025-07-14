// Cart Management for Diner POS System

class Cart {
    constructor() {
        this.items = new Map();
        this.discount = 0;
        this.taxRate = 0.10; // Default 10% tax rate
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateDisplay();
    }

    bindEvents() {
        // Add to cart buttons
        document.querySelectorAll('.add-to-cart').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const itemId = button.dataset.itemId;
                const itemName = button.dataset.itemName;
                const itemPrice = parseFloat(button.dataset.itemPrice);
                const itemStock = parseInt(button.dataset.itemStock);
                
                this.addItem(itemId, itemName, itemPrice, itemStock);
            });
        });

        // Remove from cart buttons
        document.querySelectorAll('.remove-from-cart').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const itemId = button.dataset.itemId;
                this.removeItem(itemId);
            });
        });

        // Discount input
        const discountInput = document.getElementById('discount');
        if (discountInput) {
            discountInput.addEventListener('input', (e) => {
                this.discount = parseFloat(e.target.value) || 0;
                this.updateDisplay();
            });
        }

        // Clear cart button
        const clearCartBtn = document.getElementById('clearCart');
        if (clearCartBtn) {
            clearCartBtn.addEventListener('click', () => {
                this.clearCart();
            });
        }
    }

    addItem(itemId, itemName, itemPrice, itemStock) {
        const existingItem = this.items.get(itemId);
        
        if (existingItem) {
            if (existingItem.quantity < itemStock) {
                existingItem.quantity += 1;
                existingItem.total = existingItem.quantity * existingItem.price;
            } else {
                this.showToast('Cannot add more items. Stock limit reached.', 'warning');
                return;
            }
        } else {
            if (itemStock > 0) {
                this.items.set(itemId, {
                    id: itemId,
                    name: itemName,
                    price: itemPrice,
                    quantity: 1,
                    total: itemPrice,
                    stock: itemStock
                });
            } else {
                this.showToast('Item is out of stock.', 'error');
                return;
            }
        }

        this.updateDisplay();
        this.updateItemButtons(itemId);
        this.showToast(`${itemName} added to cart`, 'success');
    }

    removeItem(itemId) {
        const item = this.items.get(itemId);
        if (item) {
            if (item.quantity > 1) {
                item.quantity -= 1;
                item.total = item.quantity * item.price;
            } else {
                this.items.delete(itemId);
            }
            
            this.updateDisplay();
            this.updateItemButtons(itemId);
            this.showToast(`${item.name} removed from cart`, 'info');
        }
    }

    updateQuantity(itemId, newQuantity) {
        const item = this.items.get(itemId);
        if (item && newQuantity > 0 && newQuantity <= item.stock) {
            item.quantity = newQuantity;
            item.total = item.quantity * item.price;
            this.updateDisplay();
            this.updateItemButtons(itemId);
        } else if (newQuantity <= 0) {
            this.items.delete(itemId);
            this.updateDisplay();
            this.updateItemButtons(itemId);
        }
    }

    clearCart() {
        this.items.clear();
        this.discount = 0;
        const discountInput = document.getElementById('discount');
        if (discountInput) {
            discountInput.value = 0;
        }
        this.updateDisplay();
        this.updateAllItemButtons();
        this.showToast('Cart cleared', 'info');
    }

    updateDisplay() {
        const cartItemsContainer = document.getElementById('cartItems');
        const cartSummary = document.getElementById('cartSummary');
        
        if (!cartItemsContainer) return;

        // Clear existing items
        cartItemsContainer.innerHTML = '';

        if (this.items.size === 0) {
            cartItemsContainer.innerHTML = `
                <div class="text-center text-muted py-3">
                    <i class="fas fa-shopping-cart fa-2x"></i>
                    <p>Cart is empty</p>
                </div>
            `;
            if (cartSummary) {
                cartSummary.style.display = 'none';
            }
            return;
        }

        // Display cart items
        this.items.forEach((item, itemId) => {
            const cartItemHtml = `
                <div class="cart-item" data-item-id="${itemId}">
                    <div class="flex-grow-1">
                        <div class="cart-item-name">${item.name}</div>
                        <div class="cart-item-details">
                            $${item.price.toFixed(2)} x ${item.quantity} = $${item.total.toFixed(2)}
                        </div>
                    </div>
                    <div class="cart-quantity-controls">
                        <button type="button" class="btn btn-sm btn-outline-danger cart-quantity-btn" 
                                onclick="cart.removeItem('${itemId}')">
                            <i class="fas fa-minus"></i>
                        </button>
                        <span class="mx-2">${item.quantity}</span>
                        <button type="button" class="btn btn-sm btn-outline-success cart-quantity-btn" 
                                onclick="cart.addItem('${itemId}', '${item.name}', ${item.price}, ${item.stock})">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                    <input type="hidden" name="item_${itemId}" value="${item.quantity}">
                </div>
            `;
            cartItemsContainer.insertAdjacentHTML('beforeend', cartItemHtml);
        });

        // Update summary
        this.updateSummary();
        
        if (cartSummary) {
            cartSummary.style.display = 'block';
        }
    }

    updateSummary() {
        const subtotal = this.getSubtotal();
        const total = this.getTotal();

        const subtotalElement = document.getElementById('subtotal');
        const totalElement = document.getElementById('total');

        if (subtotalElement) {
            subtotalElement.textContent = `$${subtotal.toFixed(2)}`;
        }
        if (totalElement) {
            totalElement.textContent = `$${total.toFixed(2)}`;
        }
    }

    updateItemButtons(itemId) {
        const quantityBadge = document.getElementById(`qty-${itemId}`);
        const addButton = document.querySelector(`[data-item-id="${itemId}"].add-to-cart`);
        const removeButton = document.querySelector(`[data-item-id="${itemId}"].remove-from-cart`);

        const item = this.items.get(itemId);
        const quantity = item ? item.quantity : 0;

        if (quantityBadge) {
            quantityBadge.textContent = quantity;
            quantityBadge.style.display = quantity > 0 ? 'inline' : 'none';
        }

        if (removeButton) {
            removeButton.style.display = quantity > 0 ? 'inline-block' : 'none';
        }

        // Update item card selection state
        const itemCard = document.querySelector(`[data-item-id="${itemId}"].item-card`);
        if (itemCard) {
            if (quantity > 0) {
                itemCard.classList.add('selected');
            } else {
                itemCard.classList.remove('selected');
            }
        }
    }

    updateAllItemButtons() {
        document.querySelectorAll('.cart-quantity').forEach(badge => {
            badge.textContent = '0';
            badge.style.display = 'none';
        });

        document.querySelectorAll('.remove-from-cart').forEach(button => {
            button.style.display = 'none';
        });

        document.querySelectorAll('.item-card').forEach(card => {
            card.classList.remove('selected');
        });
    }

    getSubtotal() {
        let subtotal = 0;
        this.items.forEach(item => {
            subtotal += item.total;
        });
        return subtotal;
    }

    getTotal() {
        const subtotal = this.getSubtotal();
        return Math.max(0, subtotal - this.discount);
    }

    getTotalWithTax() {
        const total = this.getTotal();
        return total * (1 + this.taxRate);
    }

    getItemCount() {
        let count = 0;
        this.items.forEach(item => {
            count += item.quantity;
        });
        return count;
    }

    isEmpty() {
        return this.items.size === 0;
    }

    validateCart() {
        const errors = [];
        
        if (this.isEmpty()) {
            errors.push('Cart is empty. Please add items before proceeding.');
        }

        this.items.forEach(item => {
            if (item.quantity > item.stock) {
                errors.push(`${item.name} quantity (${item.quantity}) exceeds available stock (${item.stock}).`);
            }
        });

        return errors;
    }

    showToast(message, type = 'info') {
        // Create toast notification
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : type === 'warning' ? 'warning' : 'info'} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: 3000
        });
        
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }

    // Save cart to localStorage
    saveToStorage() {
        const cartData = {
            items: Array.from(this.items.entries()),
            discount: this.discount,
            timestamp: Date.now()
        };
        localStorage.setItem('posCart', JSON.stringify(cartData));
    }

    // Load cart from localStorage
    loadFromStorage() {
        const savedCart = localStorage.getItem('posCart');
        if (savedCart) {
            try {
                const cartData = JSON.parse(savedCart);
                // Only load if saved within last hour
                if (Date.now() - cartData.timestamp < 3600000) {
                    this.items = new Map(cartData.items);
                    this.discount = cartData.discount || 0;
                    this.updateDisplay();
                    this.updateAllItemButtons();
                }
            } catch (error) {
                console.error('Error loading cart from storage:', error);
            }
        }
    }

    // Clear cart from localStorage
    clearStorage() {
        localStorage.removeItem('posCart');
    }
}

// Initialize cart when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.cart = new Cart();
    
    // Load saved cart if available
    cart.loadFromStorage();
    
    // Save cart periodically
    setInterval(() => {
        if (!cart.isEmpty()) {
            cart.saveToStorage();
        }
    }, 30000); // Save every 30 seconds
    
    // Form submission validation
    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        orderForm.addEventListener('submit', function(e) {
            const errors = cart.validateCart();
            if (errors.length > 0) {
                e.preventDefault();
                alert(errors.join('\n'));
                return false;
            }
            
            // Clear cart after successful submission
            cart.clearStorage();
        });
    }
});

// Handle page unload
window.addEventListener('beforeunload', function() {
    if (window.cart && !window.cart.isEmpty()) {
        window.cart.saveToStorage();
    }
});
