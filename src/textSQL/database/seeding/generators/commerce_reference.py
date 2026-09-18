from textSQL.database.models import (
    PaymentMethod,
    ShippingCarrier,
    ShippingMethod,
)


PAYMENT_METHODS = [
    {
        "method_name": "Visa",
        "provider_name": "Stripe",
        "method_type": "card",
    },
    {
        "method_name": "Mastercard",
        "provider_name": "Stripe",
        "method_type": "card",
    },
    {
        "method_name": "Apple Pay",
        "provider_name": "Stripe",
        "method_type": "digital_wallet",
    },
    {
        "method_name": "Mada",
        "provider_name": "HyperPay",
        "method_type": "card",
    },
    {
        "method_name": "Cash on Delivery",
        "provider_name": "Internal",
        "method_type": "cash",
    },
    {
        "method_name": "Bank Transfer",
        "provider_name": "Bank",
        "method_type": "bank_transfer",
    },
]


CARRIERS = {
    "Aramex": [
        "Standard",
        "Express",
    ],
    "DHL": [
        "Express",
    ],
    "SMSA": [
        "Standard",
        "Express",
    ],
    "FedEx": [
        "International Economy",
        "International Priority",
    ],
}


def seed_commerce_reference(session):

    if session.query(PaymentMethod).count() == 0:

        session.add_all(
            [
                PaymentMethod(**method)
                for method in PAYMENT_METHODS
            ]
        )

        session.flush()

    if session.query(ShippingCarrier).count() == 0:

        for carrier_name, methods in CARRIERS.items():

            carrier = ShippingCarrier(
                carrier_name=carrier_name
            )

            session.add(carrier)

            session.flush()

            for method_name in methods:

                session.add(
                    ShippingMethod(
                        carrier_id=carrier.carrier_id,
                        method_name=method_name,
                    )
                )

    session.commit()

    print(
        "Commerce reference data complete"
    )