"""
Base de conocimiento de FactuFácil.
Cada documento tiene 'content' y 'metadata' para el sistema RAG.
"""

FACTUFACIL_DOCUMENTS = [
    {
        "content": (
            "FactuFácil es un sistema de facturación electrónica peruano diseñado para apoyar el "
            "crecimiento de negocios. Ofrece herramientas integradas para gestión de caja, control "
            "de inventario y operaciones de punto de venta (PDV). Funciona 100% en la nube, sin "
            "instalación, accesible desde cualquier dispositivo con internet. Atiende principalmente "
            "a ferreterías, mini markets, farmacias, restaurantes y negocios retail en general. "
            "Cumple con todos los requisitos legales de SUNAT para facturación electrónica en Perú."
        ),
        "metadata": {"category": "empresa", "topic": "descripcion_general"},
    },
    {
        "content": (
            "PLANES Y PRECIOS DE FACTUFÁCIL:\n\n"
            "Plan BÁSICO — S/.45 por mes (S/.450 al año):\n"
            "- Emisión ilimitada de facturas y boletas electrónicas\n"
            "- Notas de crédito\n"
            "- Conexión directa a SUNAT\n"
            "- Validación RENIEC para clientes\n"
            "- Acceso a todos los módulos\n"
            "- Curso FactuFácil de capacitación\n"
            "- Soporte por WhatsApp\n\n"
            "Plan PRO — S/.95 por mes (S/.950 al año) — EL MÁS POPULAR:\n"
            "- Todo lo incluido en el plan Básico\n"
            "- Acceso a cursos de academia FactuFácil\n"
            "- Landing page personalizada para el negocio\n"
            "- E-commerce integrado para ventas online\n"
            "- Múltiples sucursales y series de comprobantes\n"
            "- Reportes avanzados de ventas, compras y tributación\n"
            "- Soporte prioritario\n\n"
            "Pagar anual representa un ahorro equivalente a 2 meses respecto al pago mensual."
        ),
        "metadata": {"category": "precios", "topic": "planes"},
    },
    {
        "content": (
            "COMPARATIVA DE PLANES FACTUFÁCIL:\n\n"
            "Característica                     | Básico (S/.45/mes) | PRO (S/.95/mes)\n"
            "Facturas y boletas electrónicas    | Ilimitadas          | Ilimitadas\n"
            "Notas de crédito                   | Sí                  | Sí\n"
            "Conexión a SUNAT                   | Sí                  | Sí\n"
            "Validación RENIEC                  | Sí                  | Sí\n"
            "Todos los módulos                  | Sí                  | Sí\n"
            "Curso FactuFácil                   | Sí                  | Sí\n"
            "Soporte WhatsApp                   | Sí                  | Sí\n"
            "Academia FactuFácil                | No                  | Sí\n"
            "Landing page personalizada         | No                  | Sí\n"
            "E-commerce integrado               | No                  | Sí\n"
            "Múltiples sucursales/series        | No                  | Sí\n"
            "Reportes avanzados                 | No                  | Sí\n"
            "Soporte prioritario                | No                  | Sí\n\n"
            "Precios anuales: Básico S/.450/año | PRO S/.950/año"
        ),
        "metadata": {"category": "precios", "topic": "comparativa_planes"},
    },
    {
        "content": (
            "FACTURACIÓN ELECTRÓNICA EN FACTUFÁCIL:\n\n"
            "Tipos de comprobantes disponibles:\n"
            "- Facturas electrónicas\n"
            "- Boletas de venta electrónicas\n"
            "- Notas de crédito\n"
            "- Notas de débito\n"
            "- Guías de remisión electrónicas\n\n"
            "Características:\n"
            "- Emisión ilimitada de comprobantes\n"
            "- Integración directa con SUNAT en tiempo real\n"
            "- Validación de RUC con SUNAT\n"
            "- Validación de DNI con RENIEC\n"
            "- Múltiples series para distintas sucursales (Plan PRO)\n"
            "- Código QR en todos los comprobantes\n"
            "- Envío automático al cliente por email"
        ),
        "metadata": {"category": "facturacion", "topic": "comprobantes"},
    },
    {
        "content": (
            "GESTIÓN DE INVENTARIO EN FACTUFÁCIL:\n\n"
            "- Control y monitoreo de stock en tiempo real\n"
            "- Historial de compras y movimientos\n"
            "- Metodología Pareto (análisis ABC de productos)\n"
            "- Conteo cíclico de inventario\n"
            "- Alertas de stock mínimo\n"
            "- Control de vencimientos\n"
            "- Múltiples almacenes\n\n"
            "Se integra automáticamente con los módulos de ventas y compras. "
            "Accesible desde cualquier dispositivo con internet."
        ),
        "metadata": {"category": "inventario", "topic": "gestion_inventario"},
    },
    {
        "content": (
            "PUNTO DE VENTA (PDV) EN FACTUFÁCIL:\n\n"
            "- Interfaz intuitiva para ventas rápidas\n"
            "- Integración con lector de código de barras vía celular\n"
            "- Procesamiento de transacciones en tiempo real\n"
            "- Gestión de caja y arqueo de caja\n"
            "- Múltiples métodos de pago: efectivo, tarjeta, transferencia\n"
            "- Emisión inmediata de comprobantes electrónicos\n"
            "- Impresión en impresoras térmicas\n\n"
            "No requiere hardware especializado para empezar. "
            "Ideal para ferreterías, mini markets, farmacias y restaurantes."
        ),
        "metadata": {"category": "pos", "topic": "punto_de_venta"},
    },
    {
        "content": (
            "E-COMMERCE Y VENTAS ONLINE EN FACTUFÁCIL (PLAN PRO):\n\n"
            "Incluido en el plan PRO:\n"
            "- Creación de tienda online basada en WordPress\n"
            "- Más de 30 plantillas personalizables\n"
            "- Integración con redes sociales: Facebook y Google\n"
            "- Interfaz de gestión de productos\n"
            "- Carrito de compras integrado\n"
            "- Landing page personalizada para el negocio\n\n"
            "La tienda online se sincroniza con el inventario del sistema. "
            "Permite vender por internet sin conocimientos técnicos."
        ),
        "metadata": {"category": "ecommerce", "topic": "ventas_online"},
    },
    {
        "content": (
            "GESTIÓN EMPRESARIAL, COMPRAS Y REPORTES EN FACTUFÁCIL:\n\n"
            "Módulo de compras:\n"
            "- Flujo completo: cotización → orden de compra → compra\n"
            "- Gestión de proveedores\n"
            "- Conciliación de caja\n\n"
            "Reportes avanzados (Plan PRO):\n"
            "- Reporte de ventas\n"
            "- Reporte de compras\n"
            "- Reporte de cumplimiento tributario\n"
            "- Kardex de inventario\n"
            "- Dashboard de métricas del negocio\n\n"
            "Todos los reportes pueden exportarse para análisis posterior."
        ),
        "metadata": {"category": "gestion", "topic": "compras_reportes"},
    },
    {
        "content": (
            "APLICACIÓN MÓVIL Y ACCESO EN LA NUBE — FACTUFÁCIL:\n\n"
            "- Sin instalación requerida, 100% en la nube\n"
            "- Acceso desde computadora, tablet o celular\n"
            "- Compatible con cualquier navegador web moderno\n"
            "- Facturación offline: guarda y envía a SUNAT al restaurar conexión\n"
            "- Actualizaciones automáticas sin costo adicional\n"
            "- Datos respaldados en la nube de forma segura\n\n"
            "Demo disponible sin registro:\n"
            "URL: demo.factufacil.pe\n"
            "Usuario: demo01@gmail.com\n"
            "Contraseña: 123456"
        ),
        "metadata": {"category": "app", "topic": "acceso_movil"},
    },
    {
        "content": (
            "EQUIPOS Y HARDWARE PARA FACTUFÁCIL:\n\n"
            "FactuFácil también vende equipos de punto de venta compatibles:\n"
            "- Cajones de dinero (cash drawers)\n"
            "- Impresoras térmicas para tickets y comprobantes\n"
            "- Lectores de código de barras\n"
            "- Tablets para punto de venta\n"
            "- Laptops para gestión\n"
            "- Sistemas biométricos\n\n"
            "Se puede empezar con una computadora o tablet existente, sin hardware adicional."
        ),
        "metadata": {"category": "equipos", "topic": "hardware"},
    },
    {
        "content": (
            "CONTACTO Y SOPORTE — FACTUFÁCIL:\n\n"
            "Para contratar, consultar o soporte técnico:\n"
            "- Teléfono / WhatsApp: +51 964 979 320\n"
            "- Email: ventas@factufacil.pe\n"
            "- Demo gratuita: demo.factufacil.pe\n\n"
            "Soporte según plan:\n"
            "- Plan Básico: soporte por WhatsApp\n"
            "- Plan PRO: soporte prioritario\n\n"
            "FactuFácil atiende a negocios en todo el Perú."
        ),
        "metadata": {"category": "contacto", "topic": "soporte_contacto"},
    },
    {
        "content": (
            "PREGUNTAS FRECUENTES — FACTUFÁCIL:\n\n"
            "¿Necesito instalar algo?\n"
            "No. FactuFácil es 100% en la nube. Solo necesitás un navegador web.\n\n"
            "¿Está integrado con SUNAT?\n"
            "Sí. Tiene integración directa con SUNAT para validar y enviar comprobantes.\n\n"
            "¿Puedo usar FactuFácil en mi celular?\n"
            "Sí. Funciona desde cualquier dispositivo: computadora, tablet o celular.\n\n"
            "¿Qué pasa si se va el internet?\n"
            "FactuFácil tiene modo offline. Las facturas se guardan y se envían a SUNAT "
            "automáticamente cuando se restaura la conexión.\n\n"
            "¿Cuántos comprobantes puedo emitir?\n"
            "Ilimitados. No hay restricción en ningún plan.\n\n"
            "¿Puedo tener varias sucursales?\n"
            "Sí, con el Plan PRO podés tener múltiples sucursales y series independientes.\n\n"
            "¿Incluye capacitación?\n"
            "Sí. El Plan Básico incluye el Curso FactuFácil. "
            "El Plan PRO agrega acceso completo a la Academia FactuFácil.\n\n"
            "¿Para qué negocios es ideal?\n"
            "Ferreterías, mini markets, farmacias, restaurantes y negocios retail en general."
        ),
        "metadata": {"category": "faq", "topic": "preguntas_frecuentes"},
    },
    {
        "content": (
            "SECTORES Y CASOS DE USO — FACTUFÁCIL:\n\n"
            "Ferreterías:\n"
            "- Control de inventario con miles de SKUs\n"
            "- Ventas al por mayor y menor\n"
            "- Guías de remisión para despachos\n\n"
            "Mini Markets y Bodegas:\n"
            "- PDV ágil para ventas rápidas\n"
            "- Control de stock y vencimientos\n"
            "- Lectura de código de barras con celular\n\n"
            "Farmacias:\n"
            "- Control de stock de medicamentos\n"
            "- Comprobantes electrónicos inmediatos\n\n"
            "Restaurantes:\n"
            "- Boletas y facturas en segundos\n"
            "- Gestión de caja integrada\n\n"
            "Negocios con sucursales (Plan PRO):\n"
            "- Múltiples sedes con series independientes\n"
            "- Reportes consolidados de todas las sucursales"
        ),
        "metadata": {"category": "casos_uso", "topic": "sectores"},
    },
]
