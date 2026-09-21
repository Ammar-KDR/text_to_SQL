import uuid



NAMESPACE = uuid.UUID(
    "d8b7e6b8-1f5a-4f4f-9b6a-3c7a8f2f9c01"
)



def generate_document_id(
    document_id: str,
) -> str:

    return str(
        uuid.uuid5(
            NAMESPACE,
            document_id,
        )
    )