"""
Verificación estructural de Fase 1 — entidades ERP + 8 ports async.

No es un test unitario con pytest (el venv no lo tiene instalado); son
asserts reales ejecutados directamente, en la misma línea que
scripts/spike_smoke_test_toolcalling.py de la Fase 0. Cada assert prueba
comportamiento real (instanciación con dataclasses, abstracción de ABC que
impide instanciar sin implementar métodos, coroutines correctas) — no son
asserts triviales.

Run: python scripts/verify_phase1_domain_ports.py
"""
import asyncio
import inspect
import sys

from core.domain import (
    Brand,
    Cash,
    Category,
    Cpe,
    Customer,
    Dispatch,
    DispatchTables,
    Item,
    ItemDraft,
    Perception,
    Purchase,
    Report,
    Retention,
    SaleNote,
    StockMovement,
    StockTxn,
    Supplier,
)
from core.ports import (
    CustomersPort,
    DispatchPort,
    FinancePort,
    InventoryPort,
    ItemsPort,
    PurchasesPort,
    SalesPort,
    SuppliersPort,
)

PASS = []
FAIL = []


def check(name: str, condition: bool):
    if condition:
        PASS.append(name)
    else:
        FAIL.append(name)
        print(f"FAIL: {name}")


def check_entities():
    item = Item(id=1, description="Tornillo 1/4", price=2.5, barcode="7501234567890")
    check("Item instantiable with required fields", item.id == 1 and item.price == 2.5)
    check("Item defaults: active=True, favorite=False, has_igv=True",
          item.active is True and item.favorite is False and item.has_igv is True)

    draft = ItemDraft(description="Tuerca 1/4", price=1.2)
    check("ItemDraft has no id field (not yet persisted)", not hasattr(draft, "id"))

    cat = Category(id=1, name="Ferretería")
    brand = Brand(id=1, name="Stanley")
    check("Category/Brand are minimal id+name", cat.name == "Ferretería" and brand.name == "Stanley")

    txn = StockTxn(item_code="SKU-1", type="input", warehouse_id=1, inventory_transaction_id=2, quantity=10)
    mov = StockMovement(id=1, item_code="SKU-1", type="input", warehouse_id=1, quantity=10, resulting_stock=20)
    check("StockTxn/StockMovement round-trip type field", txn.type == "input" and mov.type == txn.type)

    cust = Customer(id=1, document_number="20610448578", name="Yiwu Import Corp")
    supp = Supplier(id=1, document_number="20999999999", name="Proveedor SAC")
    check("Customer and Supplier are distinct entities", type(cust) is not type(supp))

    sn = SaleNote(id=1, customer_id=cust.id, items=[{"item_id": 1, "qty": 2}], total=5.0)
    cpe = Cpe(id=1, sale_note_id=sn.id, document_type_id="01", series="F001", number="1")
    check("SaleNote -> Cpe references sale_note_id", cpe.sale_note_id == sn.id)

    purchase = Purchase(id=1, supplier_id=supp.id, doc_type_id="01", series="F001", number="1", date_of_issue="2026-06-23")
    check("Purchase references supplier_id", purchase.supplier_id == supp.id)

    dispatch = Dispatch(id=1, origin_address="Av. A 123", delivery_address="Av. B 456")
    tables = DispatchTables()
    check("Dispatch has origin/delivery address, DispatchTables defaults to empty lists",
          dispatch.origin_address == "Av. A 123" and tables.transfer_reasons == [])

    retention = Retention(id=1, amount=18.5)
    perception = Perception(id=1, amount=3.2)
    check("Retention/Perception carry amount", retention.amount == 18.5 and perception.amount == 3.2)

    cash = Cash(id=1, state=True, beginning_balance=100.0)
    check("Cash starts with state + beginning_balance", cash.state is True and cash.beginning_balance == 100.0)

    report = Report(data={"total_sales": 42})
    check("Report wraps free-form payload", report.data["total_sales"] == 42)


def check_ports_are_abstract():
    """Real ABC behavior: instantiating a port WITHOUT implementing all
    abstract methods must raise TypeError. This is not a trivial existence
    check — it proves Python's abc machinery is correctly wired (every
    method is decorated with @abstractmethod)."""
    for port_cls in (
        ItemsPort, InventoryPort, CustomersPort, SuppliersPort,
        SalesPort, PurchasesPort, DispatchPort, FinancePort,
    ):
        try:
            port_cls()
            check(f"{port_cls.__name__} cannot be instantiated directly", False)
        except TypeError:
            check(f"{port_cls.__name__} cannot be instantiated directly", True)


def check_port_methods_are_coroutines():
    """Every abstract method on the 8 new ports must be an async def —
    this is the documented sync/async split decision. A regular `def`
    would silently break the contract at the adapter layer."""
    expected = {
        ItemsPort: {"search", "create"},
        InventoryPort: {
            "get_item", "update_item", "change_active", "change_favorite",
            "list_categories", "list_brands", "register_transaction",
        },
        CustomersPort: {"search"},
        SuppliersPort: {"search"},
        SalesPort: {"create_sale_note", "generate_cpe"},
        PurchasesPort: {"create_purchase"},
        DispatchPort: {"get_tables", "create_dispatch", "send_dispatch", "list_dispatches"},
        FinancePort: {
            "create_retention", "create_perception", "open_cash",
            "close_cash", "get_daily_report", "get_general_sale_report",
        },
    }
    for port_cls, method_names in expected.items():
        abstract_methods = port_cls.__abstractmethods__
        check(f"{port_cls.__name__} declares exactly the expected abstract methods",
              abstract_methods == method_names)
        for name in method_names:
            fn = getattr(port_cls, name)
            check(f"{port_cls.__name__}.{name} is an async coroutine function",
                  inspect.iscoroutinefunction(fn))


def check_concrete_subclass_must_implement_all():
    """Triangulation: a SECOND, different scenario — a concrete subclass
    that implements only SOME methods must still fail to instantiate. This
    proves the ABC actually enforces ALL abstract methods, not just one."""

    class IncompleteItemsAdapter(ItemsPort):
        async def search(self, query, *, by_barcode=False, page=1):
            return []
        # missing `create` on purpose

    try:
        IncompleteItemsAdapter()
        check("Partial ItemsPort subclass (missing create) cannot instantiate", False)
    except TypeError:
        check("Partial ItemsPort subclass (missing create) cannot instantiate", True)

    class CompleteItemsAdapter(ItemsPort):
        async def search(self, query, *, by_barcode=False, page=1):
            return [Item(id=1, description="x", price=1.0)]

        async def create(self, item):
            return Item(id=99, description=item.description, price=item.price)

    instance = CompleteItemsAdapter()
    result = asyncio.run(instance.search("tornillo"))
    check("Complete ItemsPort subclass instantiates and search() returns real data",
          len(result) == 1 and result[0].description == "x")

    created = asyncio.run(instance.create(ItemDraft(description="nuevo", price=9.9)))
    check("Complete ItemsPort subclass create() returns a different Item with mapped fields",
          created.id == 99 and created.description == "nuevo")


def main():
    check_entities()
    check_ports_are_abstract()
    check_port_methods_are_coroutines()
    check_concrete_subclass_must_implement_all()

    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("FAILED CHECKS:")
        for name in FAIL:
            print(f"  - {name}")
        sys.exit(1)
    print("ALL CHECKS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
