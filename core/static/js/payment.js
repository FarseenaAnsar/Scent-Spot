// Handle payment errors and redirects
function handlePaymentError(response) {
    if (response.redirect_url) {
        window.location.href = response.redirect_url;
    } else {
        alert(response.message || "Payment failed. Please try again.");
    }
}

// Update the AJAX error handlers
$(document).ready(function() {
    // For Razorpay payment errors
    $(document).on('razorpay:payment:failed', function(e) {
        const error = e.detail.error;
        window.location.href = `/payment-failure/?error_message=${encodeURIComponent(error.description)}`;
    });
    
    // For AJAX errors in payment processing
    $(document).ajaxError(function(event, jqXHR, settings, thrownError) {
        if (settings.url.includes('razorpaycheck') || settings.url.includes('verify-payment') || settings.url.includes('place-cod-order')) {
            try {
                const response = JSON.parse(jqXHR.responseText);
                handlePaymentError(response);
            } catch (e) {
                window.location.href = `/payment-failure/?error_message=${encodeURIComponent("An unexpected error occurred")}`;
            }
        }
    });
});