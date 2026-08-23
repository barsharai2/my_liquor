

document.addEventListener("DOMContentLoaded", function () {

    const ageModalElement = document.getElementById("ageModal");

    if (!ageModalElement) {
        return;
    }


    const ageVerified = localStorage.getItem("ageVerified");


    if (!ageVerified) {

        const ageModal = new bootstrap.Modal(
            ageModalElement
        );

        ageModal.show();


        const yesButton =
            document.getElementById("ageYes");

        const noButton =
            document.getElementById("ageNo");


        yesButton.addEventListener("click", function () {

            localStorage.setItem(
                "ageVerified",
                "true"
            );

            ageModal.hide();

        });


        noButton.addEventListener("click", function () {

            window.location.href =
                "https://www.google.com/";

        });

    }

});


/* =========================================================
   ADD TO CART DEMO
========================================================= */

document.addEventListener("click", function (event) {

    const button =
        event.target.closest(".add-cart");

    if (!button) {
        return;
    }


    event.preventDefault();


    const cartCount =
        document.querySelector(".cart-count");


    if (cartCount) {

        let count =
            parseInt(cartCount.textContent) || 0;

        count++;

        cartCount.textContent = count;

    }


    button.innerHTML =
        '<i class="bi bi-check-lg"></i>';


    setTimeout(function () {

        button.innerHTML =
            '<i class="bi bi-bag-plus"></i>';

    }, 1500);

});


/* =========================================================
   SEARCH
========================================================= */

const searchInput =
    document.querySelector(
        '.search-form input[type="search"]'
    );


if (searchInput) {

    searchInput.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Enter") {

                const value =
                    searchInput.value.trim();

                if (!value) {
                    event.preventDefault();
                }

            }

        }
    );

}

