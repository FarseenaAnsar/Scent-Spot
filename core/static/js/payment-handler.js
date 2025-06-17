// Handle payment responses and redirects
document.addEventListener('DOMContentLoaded', function() {
    // Add event listener to the place order button
    const placeOrderBtn = document.getElementById('place-order-btn');
    if (placeOrderBtn) {
        placeOrderBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const paymentMethod = document.querySelector('input[name="payment_method"]:checked').value;
            const form = document.getElementById('payment-form');
            
            if (paymentMethod === 'cod') {
                handleCODPayment(form);
            } else {
                handleRazorpayPayment(form);
            }
        });
    }
});

// Handle COD payment
function handleCODPayment(form) {
    const formData = new FormData(form);
    
    fetch('/place-cod-order', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.href = data.redirect_url;
        } else {
            handlePaymentError(data);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        window.location.href = '/payment-failure/?error_message=' + encodeURIComponent('Error processing your order');
    });
}

// Handle Razorpay payment
function handleRazorpayPayment(form) {
    const formData = new FormData(form);
    
    fetch('/razorpaycheck', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const options = {
            key: data.key,
            amount: data.amount,
            currency: "INR",
            name: "ScentSpot",
            description: "Purchase from ScentSpot",
            order_id: data.order_id,
            handler: function(response) {
                verifyPayment(response, form);
            },
            prefill: {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                contact: document.getElementById('phone').value
            },
            theme: {
                color: "#3399cc"
            },
            modal: {
                ondismiss: function() {
                    window.location.href = '/payment-failure/?error_message=' + encodeURIComponent('Payment cancelled by user');
                }
            }
        };
        
        const rzp = new Razorpay(options);
        rzp.on('payment.failed', function(response) {
            window.location.href = '/payment-failure/?error_message=' + encodeURIComponent(response.error.description);
        });
        rzp.open();
    })
    .catch(error => {
        console.error('Error:', error);
        window.location.href = '/payment-failure/?error_message=' + encodeURIComponent('Error processing your payment request');
    });
}

// Verify payment with server
function verifyPayment(response, form) {
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    
    const verifyData = new FormData();
    verifyData.append('payment_id', response.razorpay_payment_id);
    verifyData.append('order_id', response.razorpay_order_id);
    verifyData.append('signature', response.razorpay_signature);
    verifyData.append('address', document.getElementById('address').value);
    verifyData.append('phone', document.getElementById('phone').value);
    verifyData.append('fname', document.getElementById('name').value);
    verifyData.append('email', document.getElementById('email').value);
    verifyData.append('csrfmiddlewaretoken', csrfToken);
    
    fetch('/verify-payment', {
        method: 'POST',
        body: verifyData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.href = '/payment-success/' + response.razorpay_payment_id + '/';
        } else {
            handlePaymentError(data);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        window.location.href = '/payment-failure/?error_message=' + encodeURIComponent('Payment verification failed');
    });
}

// Handle payment errors
function handlePaymentError(response) {
    if (response.redirect_url) {
        window.location.href = response.redirect_url;
    } else {
        window.location.href = '/payment-failure/?error_message=' + encodeURIComponent(response.message || 'Payment failed');
    }
}