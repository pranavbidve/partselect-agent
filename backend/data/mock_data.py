MOCK_CUSTOMERS = {
    "CUST-001": {
        "name": "John Smith",
        "account_tier": "standard",
        "order_history": [
            {"order_id": "ORD-4821", "part": "PS11752389", "part_name": "Refrigerator Ice Maker Replacement", "date": "2024-11-10", "status": "delivered"},
            {"order_id": "ORD-4103", "part": "PS11723179", "part_name": "Water Inlet Valve", "date": "2024-08-22", "status": "delivered"},
            {"order_id": "ORD-5102", "part": "PS16218782", "part_name": "Refrigerator Water Filter", "date": "2025-01-15", "status": "delivered"},
        ],
        "open_tickets": [
            {"ticket_id": "TKT-2201", "issue": "Dishwasher drain issue — awaiting part delivery", "status": "in progress"},
        ],
        "email": "j.smith@email.com",
    },
    "CUST-002": {
        "name": "Maria Garcia",
        "account_tier": "premium",
        "order_history": [
            {"order_id": "ORD-5501", "part": "PS11755472", "part_name": "Dishwasher Pump and Motor Assembly", "date": "2025-02-03", "status": "delivered"},
            {"order_id": "ORD-5489", "part": "PS11745603", "part_name": "Dishwasher Water Inlet Valve", "date": "2025-01-28", "status": "delivered"},
        ],
        "open_tickets": [],
        "email": "m.garcia@email.com",
    },
    "CUST-003": {
        "name": "Bob Johnson",
        "account_tier": "standard",
        "order_history": [
            {"order_id": "ORD-4677", "part": "PS11737119", "part_name": "Evaporator Fan Motor", "date": "2024-09-14", "status": "delivered"},
        ],
        "open_tickets": [
            {"ticket_id": "TKT-2198", "issue": "Refrigerator not cooling — service visit scheduled", "status": "open"},
        ],
        "email": "b.johnson@email.com",
    },
}

WAREHOUSE_SHIPPING_DAYS = {
    "Detroit-MI": 2,
    "Chicago-IL": 3,
    "Atlanta-GA": 4,
    "Dallas-TX":  4,
    "Seattle-WA": 5,
    "Phoenix-AZ": 4,
}

MOCK_INVENTORY = {
    # Low stock (triggers recommendation agent)
    "PS11752389": {"stock_level": 3, "warehouse": "Detroit-MI",  "restock_eta": "2026-06-04"},
    "PS3617225":  {"stock_level": 2, "warehouse": "Chicago-IL",  "restock_eta": "2026-06-09"},
    "PS1021960":  {"stock_level": 4, "warehouse": "Atlanta-GA",  "restock_eta": "2026-06-07"},
    "PS17139830": {"stock_level": 1, "warehouse": "Dallas-TX",   "restock_eta": "2026-06-02"},
    "PS11766745": {"stock_level": 3, "warehouse": "Detroit-MI",  "restock_eta": "2026-06-11"},
    "PS11765780": {"stock_level": 4, "warehouse": "Chicago-IL",  "restock_eta": "2026-06-16"},
    "PS12349161": {"stock_level": 2, "warehouse": "Seattle-WA",  "restock_eta": "2026-06-23"},
    "PS8764501":  {"stock_level": 4, "warehouse": "Phoenix-AZ",  "restock_eta": "2026-06-13"},
    # In stock
    "PS11709611": {"stock_level": 12, "warehouse": "Chicago-IL",  "restock_eta": None},
    "PS11754529": {"stock_level": 8,  "warehouse": "Atlanta-GA",  "restock_eta": None},
    "PS11723179": {"stock_level": 15, "warehouse": "Detroit-MI",  "restock_eta": None},
    "PS2323273":  {"stock_level": 20, "warehouse": "Chicago-IL",  "restock_eta": None},
    "PS12754394": {"stock_level": 18, "warehouse": "Dallas-TX",   "restock_eta": None},
    "PS11737119": {"stock_level": 7,  "warehouse": "Atlanta-GA",  "restock_eta": None},
    "PS3502361":  {"stock_level": 9,  "warehouse": "Detroit-MI",  "restock_eta": None},
    "PS6883666":  {"stock_level": 11, "warehouse": "Chicago-IL",  "restock_eta": None},
    "PS11743535": {"stock_level": 6,  "warehouse": "Dallas-TX",   "restock_eta": None},
    "PS11739991": {"stock_level": 14, "warehouse": "Atlanta-GA",  "restock_eta": None},
    "PS17139815": {"stock_level": 5,  "warehouse": "Chicago-IL",  "restock_eta": None},
    "PS16227369": {"stock_level": 8,  "warehouse": "Detroit-MI",  "restock_eta": None},
    "PS2358826":  {"stock_level": 16, "warehouse": "Dallas-TX",   "restock_eta": None},
    "PS11738202": {"stock_level": 22, "warehouse": "Chicago-IL",  "restock_eta": None},
    "PS11742479": {"stock_level": 10, "warehouse": "Atlanta-GA",  "restock_eta": None},
    "PS8689661":  {"stock_level": 13, "warehouse": "Detroit-MI",  "restock_eta": None},
    "PS11739983": {"stock_level": 7,  "warehouse": "Seattle-WA",  "restock_eta": None},
    "PS16218782": {"stock_level": 25, "warehouse": "Chicago-IL",  "restock_eta": None},
    "PS8746145":  {"stock_level": 30, "warehouse": "Dallas-TX",   "restock_eta": None},
    "PS3412266":  {"stock_level": 19, "warehouse": "Atlanta-GA",  "restock_eta": None},
    "PS11775596": {"stock_level": 11, "warehouse": "Detroit-MI",  "restock_eta": None},
    "PS1766247":  {"stock_level": 9,  "warehouse": "Chicago-IL",  "restock_eta": None},
    "PS3523330":  {"stock_level": 14, "warehouse": "Dallas-TX",   "restock_eta": None},
    "PS3501052":  {"stock_level": 6,  "warehouse": "Atlanta-GA",  "restock_eta": None},
    "PS11755472": {"stock_level": 17, "warehouse": "Chicago-IL",  "restock_eta": None},
    "PS1765984":  {"stock_level": 20, "warehouse": "Detroit-MI",  "restock_eta": None},
    "PS8737036":  {"stock_level": 23, "warehouse": "Dallas-TX",   "restock_eta": None},
    "PS11745603": {"stock_level": 16, "warehouse": "Chicago-IL",  "restock_eta": None},
    "PS16729156": {"stock_level": 8,  "warehouse": "Atlanta-GA",  "restock_eta": None},
    "PS3633113":  {"stock_level": 12, "warehouse": "Detroit-MI",  "restock_eta": None},
    "PS12582725": {"stock_level": 7,  "warehouse": "Chicago-IL",  "restock_eta": None},
    "PS11731570": {"stock_level": 28, "warehouse": "Dallas-TX",   "restock_eta": None},
    "PS8732952":  {"stock_level": 15, "warehouse": "Atlanta-GA",  "restock_eta": None},
    "PS12745420": {"stock_level": 21, "warehouse": "Detroit-MI",  "restock_eta": None},
    "PS11760658": {"stock_level": 9,  "warehouse": "Chicago-IL",  "restock_eta": None},
    "PS11756150": {"stock_level": 18, "warehouse": "Dallas-TX",   "restock_eta": None},
}
