$(document).ready(function(){
    $(".payWithRazorPay").click(function(e){
        e.preventDefault();
        let fname = $("[name='fname']").val();
        let email = $("[name='email']").val();
        let phone = $("[name='phone']").val();
        let address = $("[name='address']").val();
        let total = $("[name='total']").val();
        if (fname == "" || email == "" || phone =="" || address == "" || total =="")
        {
            alert("All fields are mandatory!")
            return false;
        }
        else
        {
            $.ajax({
                method: "POST",
                url: "proceed-to-pay",
                success: function(response){
                    //console.log(response.total)
                    var options = {
                        "key": "rzp_test_ntpJZaqX4joGj8", // Enter the Key ID generated from the Dashboard
                        "amount": response.total, // Amount is in currency subunits. Default currency is INR. Hence, 50000 refers to 50000 paise
                        "currency": "INR",
                        "name": "Scent Spot",
                        "description": "We're deeply grateful for your patronage,",
                        "image": "https://example.com/your_logo",
                        //"order_id": "order_IluGWxBm9U8zJ8", //This is a sample Order ID. Pass the `id` obtained in the response of Step 1
                        "handler": function (response){
                            alert(response.razorpay_payment_id);
                            
                        },
                        "prefill": {
                            "name": fname,
                            "email": email,
                            "contact": phone
                        },
            
                        "theme": {
                            "color": "#3399cc"
                        }
                    };
                    var rzp1 = new Razorpay(options);
                    rzp1.on('payment.failed', function (response){
                        alert(response.error.description);
                    });
                    rzp1.open();
                }
            });
            
        }

       
    });
});

function handlePaymentSuccess(response) {
    // Send payment verification to your backend
    $.ajax({
        method: "POST",
        url: "/verify-payment/",
        headers: {
            'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
        },
        data: {
            'payment_id': response.razorpay_payment_id,
            'order_id': response.razorpay_order_id,
            'signature': response.razorpay_signature,
            'amount': response.total
        },
        success: function(serverResponse){
            if(serverResponse.status === "success") {
                window.location.href = '/payment-success/' + response.razorpay_payment_id;
            }
        },
        error: function() {
            alert("Payment verification failed. Please contact support.");
        }
    });
}
