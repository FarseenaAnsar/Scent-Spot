$(document).ready(function(){
    $(".payWithRazorPay").click(function(e){
        e.preventDefault();
        let fname = $("[name='fname']").val();
        let email = $("[name='email']").val();
        let phone = $("[name='phone']").val();
        let address = $("[name='address']").val();
        let total = $("[name='total']").val();
        let paymentMethod = $("input[name='payment_method']:checked").val();
        if (fname == "" || email == "" || phone =="" || address == "" || total =="")
        {
            alert("All fields are mandatory!")
            return false;
        }
        else
        {
            // If COD is selected
            if (paymentMethod === "cod") {
                $.ajax({
                    method: "POST",
                    url: "/Place-cod-order/",
                    data: {
                        "fname": fname,
                        "email": email,
                        "phone": phone,
                        "address": address,
                        "total": total,
                        "payment_mode": "Cash on Delivery",
                        "payment_id": "COD-" + Date.now(),
                        "csrfmiddlewaretoken": $('input[name="csrfmiddlewaretoken"]').val()
                    },
                    headers: {
                        'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
                    },
                    success: function(response) {
                        if(response.status === "success") {
                            alert("Your COD order has been placed successfully!");
                            window.location.href = response.redirect_url;
                        } else {
                            alert("Something went wrong. Please try again.");
                        }
                    },
                    error: function(xhr, status, error) {
                        alert("Error processing your order: " + error);
                        console.log(xhr.responseText);
                    }
                });
                return;
            }
            else{
                //online payment
                $.ajax({
                    method: "POST",
                    url: "proceed-to-pay",
                    headers: {
                        'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
                    },
                    data: {
                        "total": total * 100  // Convert to paise
                    },
                    success: function(response){
                        // Razorpay payment flow
                        var options = {
                            "key": "rzp_test_ntpJZaqX4joGj8",
                            "amount": response.total,
                            "currency": "INR",
                            "name": "Scent Spot",
                            "description": "We're deeply grateful for your patronage,",
                            "image": "https://example.com/your_logo",
                            "handler": function (response){
                                // Handle successful payment
                                data = {
                                    "fname": fname,
                                    "email": email,
                                    "phone": phone,
                                    "address": address,
                                    "total": total,
                                    "payment_mode": "Paid by Razorpay",
                                    "payment_id": response.razorpay_payment_id,
                                    "csrfmiddlewaretoken": $('input[name="csrfmiddlewaretoken"]').val()
                                }
                                $.ajax({
                                    method: "POST",
                                    url: "payment-success",
                                    data: data,
                                    success: function(response){
                                        window.location.href = '/payment-success/' + response.payment_id;
                                    }
                                });
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
                        rzp1.open();
                    }
                });
            }
        }
    });
});