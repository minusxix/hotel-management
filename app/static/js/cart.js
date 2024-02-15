function addToCart(id, name, price) {
    fetch('/api/cart', {
        method: "POST",
        body: JSON.stringify({
            "id": id,
            "name": name,
            "price": price
        }),
        headers: {
            'Content-Type': "application/json"
        }
    }).then(function(res) {
        return res.json();
    }).then(function(data) {
        console.info(data)
        let c = document.getElementsByClassName('cart-counter');
        for (let d of c)
            d.innerText = data.total_quantity
    })
}
function updateCart(id, obj) {
//    document.getElementById("check_out").value = ''; //calculateTotalAmount()
    obj.disabled = true;
    fetch(`/api/cart/${id}`, {
        method: 'PUT',
        body: JSON.stringify({
            'quantity': obj.value
        }),  headers: {
            'Content-Type': "application/json"
        }
    }).then(res => res.json()).then(data => {
        obj.disabled = false;
        let c = document.getElementsByClassName('cart-counter');
        for (let d of c)
            d.innerText = data.total_quantity

        let ca = document.getElementsByClassName('cart-amount');
        for (let d of ca)
            d.innerText = data.total_amount
    });
}
function deleteCart(id, obj) {
    if (confirm("Bạn có chắc chắn xóa không?") === true) {
        obj.disabled = true;
        fetch(`/api/cart/${id}`, {
            method: 'DELETE'
        }).then(res => res.json()).then(data => {
            obj.disabled = false;
            let c = document.getElementsByClassName('cart-counter');
            for (let d of c)
                d.innerText = data.total_quantity

            let ca = document.getElementsByClassName('cart-amount');
            for (let d of ca)
                d.innerText = data.total_amount

            let r = document.getElementById(`cart${id}`);
            r.style.display = "none";
        });
    }
}
function pay() {
    const container = document.getElementById('data-container');
    const maxValue = container.dataset.maxValue;
    const checkIn = document.getElementById('check_in').value;
    const checkOut = document.getElementById('check_out').value;
    const customerData = [];
    for (let i = 0; i < maxValue; i++) {
        const customerName = document.getElementById(`customer_name_${i}`).value;
        const typeID = document.getElementById(`type_id_${i}`).value;
        const identification = document.getElementById(`identification_${i}`).value;
        const address = document.getElementById(`address_${i}`).value;
        customerData.push({
            customer_name: customerName,
            type_id: typeID,
            identification: identification,
            address: address,
            check_in: checkIn,
            check_out: checkOut
        });
    }
    if (confirm("Bạn chắc chắn thanh toán không?") == true) {
        fetch("/api/pay", {
            method: "POST",
            body: JSON.stringify({
                customers: customerData
            }),
            headers: {
                'Content-Type': "application/json"
            }
        }).then(res => res.json()).then(data => {
            if (data.status === 200)
                location.reload()
            else
                alert("Hệ thống đang bị lỗi!")
        })
    }
}




