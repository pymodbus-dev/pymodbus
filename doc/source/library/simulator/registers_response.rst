.. code-block:: json

    {
        "result": "ok",
        "footer": "Operation completed successfully",
        "register_types": {
            "bits": 1,
            "uint16": 2,
            "uint32": 3,
            "float32": 4,
            "string": 5,
            "next": 6,
            "invalid": 0
        },
        "register_actions": {
            "null": 0,
            "increment": 1,
            "random": 2,
            "reset": 3,
            "timestamp": 4,
            "uptime": 5
        },
        "register_rows": [
            {
                "index": "16",
                "type": "uint16",
                "access": "True",
                "action": "none",
                "value": "3124",
                "count_read": "0",
                "count_write": "0"
            }
        ]
    }