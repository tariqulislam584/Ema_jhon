
import json
import urllib.request
import math
import flet as ft

PRODUCTS_JSON_URL = "https://raw.githubusercontent.com/MDAnwarHossen/ema-john/refs/heads/main/products.json"
COLORS = getattr(ft, "colors", getattr(ft, "Colors", None))

# ImageFit compatibility
try:
    from flet import ImageFit  # type: ignore
    FIT_CONTAIN = ImageFit.CONTAIN
except Exception:
    try:
        from flet_core import ImageFit  # type: ignore
        FIT_CONTAIN = ImageFit.CONTAIN
    except Exception:
        FIT_CONTAIN = "contain"

# --- GLOBAL STATE (Used by nested handler functions) ---
is_logged_in = False
# Tracks where the user should go after a successful login: "home" or "checkout"
login_redirect_target = "home"
# -------------------------------------------------------


def safe_load_products(url=PRODUCTS_JSON_URL, timeout=8):
    """Loads product data from a remote JSON file with basic data cleaning."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            cleaned = []
            for i, p in enumerate(data):
                cleaned.append({
                    "id": str(p.get("id", i)),
                    "name": p.get("name", "Unnamed product"),
                    "price": float(p.get("price", 0)),
                    "img": p.get("img", "") or p.get("image", ""),
                    "category": p.get("category", ""),
                    "seller": p.get("seller", ""),
                    "stock": int(p.get("stock", p.get("quantity", 10) or 0)),
                    "ratings": float(p.get("ratings", p.get("rating", 0)) or 0),
                    "ratingsCount": int(p.get("ratingsCount", p.get("ratingCount", 0) or 0)),
                    "shipping": float(p.get("shipping", 0) or 0),
                })
            return cleaned
    except Exception as e:
        print("Warning: failed to load remote products:", e)
        # Fallback data
        return [
            {"id": "f1", "name": "Headphones, Premium Studio Quality", "price": 199.99,
             "img": "https://via.placeholder.com/220x160?text=Headphones", "stock": 10, "ratings": 4.8, "ratingsCount": 340, "shipping": 5.0},
            {"id": "f2", "name": "Ceramic Coffee Mug with Ergonomic Handle", "price": 7.50,
             "img": "https://via.placeholder.com/220x160?text=Mug", "stock": 15, "ratings": 4.6, "ratingsCount": 80, "shipping": 3.0},
            {"id": "f3", "name": "4K Ultra HD Webcam with Auto-Focus", "price": 89.99,
             "img": "https://via.placeholder.com/220x160?text=Webcam", "stock": 5, "ratings": 4.1, "ratingsCount": 120, "shipping": 4.5},
            {"id": "f4", "name": "Mechanical Keyboard, RGB Backlit", "price": 120.00,
             "img": "https://via.placeholder.com/220x160?text=Keyboard", "stock": 25, "ratings": 4.9, "ratingsCount": 550, "shipping": 6.0},
            {"id": "f5", "name": "Wireless Charging Pad, Fast Charge", "price": 25.00,
             "img": "https://via.placeholder.com/220x160?text=Charger", "stock": 30, "ratings": 4.3, "ratingsCount": 90, "shipping": 2.0},
        ]


def star_str(rating):
    """Generates a string of stars based on the rating value."""
    full = "★" * int(math.floor(rating))
    empty = "☆" * max(0, 5 - int(math.floor(rating)))
    return full + empty


# Main content area where the different views (Home, About, etc.) are rendered
main_content = ft.Column(expand=True, spacing=12)


def main(page: ft.Page):
    page.title = "EMA-JOHN"
    page.scroll = "auto"
    page.window_width = 1000
    page.window_height = 800
    page.vertical_alignment = ft.MainAxisAlignment.START

    # Initialize snack_bar properly on the page
    page.snack_bar = ft.SnackBar(
        ft.Text(""),
        duration=2000,
        bgcolor=COLORS.GREEN_ACCENT_700,
    )

    try:
        page.bgcolor = COLORS.GREY_100
    except Exception:
        pass

    products = safe_load_products()
    cart = {}

    # Login controls (defined globally in main so handler can access values)
    login_username = ft.TextField(
        label="Username", height=40, content_padding=8)
    login_email = ft.TextField(label="Email", height=40, content_padding=8)
    login_password = ft.TextField(
        label="Password", password=True, can_reveal_password=True, height=40, content_padding=8)

    # UI Controls for dynamic text
    cart_count_txt = ft.Text(f"({len(cart)})", weight=ft.FontWeight.BOLD)
    product_count_txt = ft.Text(f"({len(products)} items)", color=COLORS.GREY)

    # Initialize sign_in_btn with a base style object
    sign_in_btn = ft.ElevatedButton(
        "Sign In",
        on_click=lambda e: navigate_to_login_or_logout(),
        style=ft.ButtonStyle(
            bgcolor=COLORS.BLUE_400,  # Initial color
            color=COLORS.WHITE,
            padding=ft.padding.symmetric(horizontal=10)
        )
    )

    # Controls
    search_input = ft.TextField(
        hint_text="Search products...", col={"md": 10, "sm": 9}, height=40, content_padding=8)

    sort_dropdown = ft.Dropdown(col={"md": 2, "sm": 3}, value="Relevance", options=[
        ft.dropdown.Option("Relevance"),
        ft.dropdown.Option("Price: Low → High"),
        ft.dropdown.Option("Price: High → Low"),
        ft.dropdown.Option("Top Rated"),
    ])

    # Columns passed into ResponsiveRow
    products_column = ft.Column(spacing=8, expand=True)
    cart_column = ft.Column(spacing=8, expand=True)

    subtotal_txt = ft.Text("Subtotal: €0.00", weight=ft.FontWeight.BOLD)
    shipping_txt = ft.Text("Shipping: €0.00")
    total_txt = ft.Text(
        "Total: €0.00", weight=ft.FontWeight.BOLD, size=18, color=COLORS.RED_700)

    # Using ResponsiveRow for product grid
    products_row = ft.ResponsiveRow(run_spacing=15, spacing=15, expand=True)
    cart_listview = ft.ListView(expand=True, spacing=6, padding=6)

    # --- Robust SnackBar Helper Function ---
    def show_message(message: str, color=COLORS.GREEN_700):
        """Displays a message using the page's SnackBar control."""
        if page.snack_bar is None:
            # Should not happen if initialized at start, but defensive
            page.snack_bar = ft.SnackBar(
                ft.Text(message), duration=2000, bgcolor=color)

        page.snack_bar.content = ft.Text(message, color=COLORS.WHITE)
        page.snack_bar.bgcolor = color
        page.snack_bar.open = True
        page.update()
    # --- End SnackBar Helper ---

    # --- Navigation and Login Handlers ---

    def update_sign_in_ui():
        """Updates the Sign In button text based on login status."""
        global is_logged_in
        sign_in_btn.text = "Logout" if is_logged_in else "Sign In"
        sign_in_btn.style.bgcolor = COLORS.RED_700 if is_logged_in else COLORS.BLUE_400
        page.update()

    def navigate_to_login_or_logout(e=None):
        """Handles the header Sign In/Logout button click."""
        global is_logged_in
        global login_redirect_target
        if is_logged_in:
            # Logout logic
            is_logged_in = False
            update_sign_in_ui()
            show_message("You have been signed out.", COLORS.GREEN_700)
            render_home()
        else:
            # Go to Login page (Target is HOME if logging in via the header button)
            login_redirect_target = "home"
            render_login()

    def navigate_to_checkout(e=None):
        """Checks login status and navigates to Login or Place Order page."""
        global is_logged_in
        global login_redirect_target
        if len(cart) == 0:
            show_message(
                "Your cart is empty. Please add products first.", COLORS.AMBER_700)
            return

        if is_logged_in:
            render_place_order()
        else:
            # Go to Login page (Target is CHECKOUT if logging in via the checkout button)
            login_redirect_target = "checkout"
            render_login()

    def handle_login(e):
        """Simulates login, updates state, and redirects based on pre-login context."""

        # Simple validation
        if not login_username.value or not login_email.value or not login_password.value:
            show_message("Please fill in all fields.", COLORS.RED_500)
            return

        # Simulated successful login
        global is_logged_in
        global login_redirect_target
        is_logged_in = True
        update_sign_in_ui()

        # --- FIXED REDIRECTION LOGIC ---
        if login_redirect_target == "checkout":
            show_message(
                "Login successful! Redirecting to Finalize Order.", COLORS.GREEN_700)
            render_place_order()
        else:
            # User logged in via the header button
            show_message("Login successful! Welcome back.", COLORS.GREEN_700)
            render_home()  # Redirect to home as requested

        # Reset target after use
        login_redirect_target = "home"
        # --- END FIXED LOGIC ---

    def handle_place_order(e):
        """
        Final order placement action. 
        FIX: Capture the total before clearing the cart.
        """
        # 1. CAPTURE the current total string before we clear the cart
        final_total_charged = total_txt.value

        show_message(
            "Order #12345 confirmed! Thank Tyou for shopping with EMA-JOHN.", COLORS.PURPLE_700)

        # 2. After placing order, clear cart and refresh UI (this resets total_txt)
        cart.clear()
        refresh_cart_ui()

        # 3. Pass the captured total to the confirmation screen
        render_order_confirmation(final_total_charged)

        page.update()

    # --- End Navigation and Login Handlers ---

    # Cart helpers

    def recalc_totals():
        subtotal = sum(e["product"]["price"] * e["qty"] for e in cart.values())
        shipping = sum(e["product"].get("shipping", 0) * e["qty"]
                       for e in cart.values())
        subtotal_txt.value = f"Subtotal: €{subtotal:,.2f}"
        shipping_txt.value = f"Shipping: €{shipping:,.2f}"
        total_txt.value = f"Total: €{(subtotal + shipping):,.2f}"

    def change_qty(pid, delta):
        """Adjust quantity for product id `pid` by `delta` (±1). Remove item when qty <= 0."""
        entry = cart.get(pid)
        if not entry:
            return
        # enforce integer
        entry["qty"] = int(entry["qty"]) + int(delta)
        # respect stock if available
        stock = entry["product"].get("stock", None)
        if stock is not None and entry["qty"] > stock:
            entry["qty"] = stock
            show_message("Reached available stock limit", COLORS.RED_500)
            return
        if entry["qty"] <= 0:
            del cart[pid]
        refresh_cart_ui()

    def refresh_cart_ui():
        cart_listview.controls.clear()
        if not cart:
            cart_listview.controls.append(
                ft.Text("Your cart is empty", italic=True, color=COLORS.GREY_600))
        else:
            for pid, entry in cart.items():
                p = entry["product"]
                q = entry["qty"]

                # Left: small image thumbnail
                img = ft.Container(
                    ft.Image(src=p.get("img", ""), width=60,
                             height=60, fit=FIT_CONTAIN),
                    width=60, height=60,
                    border_radius=4,
                    bgcolor=COLORS.WHITE,
                )

                # Truncate name to fit cart view
                raw_name = p.get("name", "Unnamed")
                display_name = (
                    raw_name[:20] + "...") if len(raw_name) > 20 else raw_name

                # Middle column: truncated name + unit price
                name_price = ft.Column(
                    [
                        ft.Text(display_name, max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS, size=13),
                        ft.Text(f"€{p.get('price', 0):,.2f}", size=12,
                                weight=ft.FontWeight.BOLD, color=COLORS.RED_400),
                    ],
                    tight=True,
                    spacing=2,
                    expand=True
                )

                # Qty controls
                qty_controls = ft.Row(
                    [
                        ft.IconButton(
                            ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_size=18, tooltip="Decrease Quantity",
                            on_click=lambda e, pid=pid: change_qty(pid, -1)),
                        ft.Text(
                            str(q), width=20, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD),
                        ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_size=18, tooltip="Increase Quantity",
                                      on_click=lambda e, pid=pid: change_qty(pid, +1)),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=0,
                )

                # Right: line total
                line_total = ft.Text(
                    f"€{p.get('price', 0) * q:,.2f}", weight=ft.FontWeight.BOLD, size=13)

                # Construct row (Image | Name/Price | Qty Controls | Total)
                row = ft.Row(
                    [img, name_price, qty_controls],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )

                # Add total price below for better readability on small screens
                total_container = ft.Container(
                    content=ft.Row([ft.Text("Line Total:", size=11),
                                    line_total], alignment=ft.MainAxisAlignment.END),
                    padding=ft.padding.only(top=4, bottom=8)
                )

                cart_listview.controls.append(
                    ft.Container(
                        ft.Column([row, total_container]),
                        padding=6,
                        border=ft.border.only(
                            bottom=ft.border.BorderSide(1, COLORS.GREY_300))
                    )
                )

        cart_count_txt.value = f"({len(cart)})"
        recalc_totals()
        page.update()

    def add_to_cart(p):
        pid = p["id"]
        entry = cart.get(pid)
        if entry:
            # Check stock before adding
            stock = p.get("stock", 0)
            if entry["qty"] + 1 > stock:
                show_message(
                    "Cannot add more; reached available stock limit", COLORS.RED_500)
                return
            entry["qty"] += 1
        else:
            cart[pid] = {"product": p, "qty": 1}

        show_message(f"Added {p['name']} to cart!", COLORS.GREEN_700)
        refresh_cart_ui()

    # ---------- Product card builder: Simplified for grid view ----------

    def build_product_card(p, img_size):
        # Image is always displayed above details in a vertical stack (Column)
        image_box = ft.Container(
            content=ft.Image(src=p["img"], width=img_size,
                             height=img_size * 0.7, fit=FIT_CONTAIN),  # Adjusted height for image aspect
            padding=8,
            bgcolor=COLORS.WHITE,
            border_radius=4,
        )
        details = ft.Column([
            ft.Text(p["name"], weight=ft.FontWeight.W_600,
                    max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, size=15),
            ft.Text(f"€{p['price']:,.2f}", weight=ft.FontWeight.BOLD,
                    size=17, color=COLORS.RED_700),
            ft.Text(star_str(p.get("ratings", 0)) +
                    f" ({p.get('ratingsCount', 0)})", size=12, color=COLORS.AMBER_700),
            ft.Text(f"Seller: {p.get('seller', '-')} | Stock: {p.get('stock', 0)}",
                    size=11, color=COLORS.GREY_600),
            ft.Container(height=4),  # Spacer
            ft.ElevatedButton(
                "Add to cart",
                icon=ft.Icons.ADD_SHOPPING_CART,
                on_click=lambda e, prod=p: add_to_cart(prod),
                style=ft.ButtonStyle(
                    bgcolor="#ffd814",
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    color=COLORS.BLACK,
                    shape=ft.RoundedRectangleBorder(radius=4)
                )
            ),
        ], expand=True, spacing=4)

        # Content is always vertically stacked (image above details) for the grid
        content = ft.Column([image_box, details], spacing=8,
                            horizontal_alignment=ft.CrossAxisAlignment.START)

        tile = ft.Container(
            content=content,
            padding=12,
            bgcolor=COLORS.WHITE,
            border=ft.border.all(1, COLORS.GREY_300),
            border_radius=8,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3,
                                color=COLORS.BLACK12, offset=ft.Offset(0, 1)),
        )
        return tile

    # Helper to compute a sensible image size for the card
    def compute_img_size(page_width):
        share = page_width

        # Determine how many items per row based on breakpoints of the main layout
        if share >= 1200:  # xl: 4 items per row (9/12 column share)
            column_width_share = 9/12
            items_per_row = 4
        elif share >= 900:  # md: 3 items per row (8/12 column share)
            column_width_share = 8/12
            items_per_row = 3
        else:  # sm/xs: 2 items per row (12/12 column share)
            column_width_share = 1.0
            items_per_row = 2

        # Available space for products column (subtract overall padding 2*12)
        available_col_width = max(
            200, int(page_width * column_width_share) - 24)

        # Approximate card width
        card_width_approx = available_col_width / items_per_row

        # Target image width: ~90% of the card width, or a max of 220px
        img = int(min(220, card_width_approx * 0.90))
        return max(100, img)

    def render_products(list_of_products):
        # compute image size from current page width
        page_w = getattr(page, "window_width", None) or getattr(
            page, "client_width", None) or getattr(page, "width", None) or 1000
        img_size = compute_img_size(int(page_w))

        products_row.controls.clear()

        for p in list_of_products:
            # Wrap the product card in a Container that defines its ResponsiveRow properties
            # xs=6: 2 items per row (mobile) | md=4: 3 items per row | xl=3: 4 items per row
            products_row.controls.append(
                ft.Container(
                    content=build_product_card(p, img_size),
                    col={"xs": 6, "sm": 6, "md": 4, "xl": 3},
                )
            )
        page.update()

    def render_home():
        main_content.controls.clear()
        main_content.controls.append(build_responsive_layout())
        page.update()

    def render_order_review():
        # Recalculate totals to ensure accurate display
        recalc_totals()

        main_content.controls.clear()
        main_content.controls.append(ft.Container(
            ft.Column([
                ft.Text("Order Review", weight=ft.FontWeight.BOLD,
                        size=24, color=COLORS.GREY_800),
                ft.Divider(),
                ft.Text(
                    "Review your cart items and shipping details before proceeding to payment."),
                ft.Container(content=cart_listview, expand=True,
                             # Set height for better layout
                             padding=ft.padding.only(top=10), height=300),
                ft.Divider(),
                subtotal_txt, shipping_txt, total_txt,
                ft.ElevatedButton("Proceed to Payment", on_click=navigate_to_checkout,
                                  # Disable if cart is empty
                                  disabled=len(cart) == 0,
                                  style=ft.ButtonStyle(
                                      bgcolor=COLORS.GREEN_600, color=COLORS.WHITE),
                                  expand=True),
                ft.TextButton("Continue Shopping",
                              on_click=lambda e: render_home())
            ], spacing=8),
            padding=20,
            bgcolor=COLORS.WHITE,
            border_radius=10,
            expand=True
        ))
        page.update()

    def render_login():
        main_content.controls.clear()
        main_content.controls.append(ft.Container(
            ft.Column([
                ft.Text("Sign In to Checkout", weight=ft.FontWeight.BOLD,
                        size=24, color=COLORS.BLUE_700),
                ft.Divider(),
                ft.Text(
                    "Please log in with your credentials to finalize your order.", color=COLORS.GREY_700),
                ft.Container(height=10),
                login_username,
                login_email,
                login_password,
                ft.Container(height=10),
                ft.ElevatedButton(
                    "Login & Proceed",
                    icon=ft.Icons.LOCK_OPEN_OUTLINED,
                    on_click=handle_login,
                    style=ft.ButtonStyle(
                        bgcolor=COLORS.GREEN_600, color=COLORS.WHITE, padding=15
                    )
                ),
                ft.TextButton("Back to Order Review",
                              on_click=lambda e: render_order_review())
            ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.START),
            padding=40,
            bgcolor=COLORS.WHITE,
            border_radius=10,
            width=500,  # Constrain width for a better form look
            alignment=ft.alignment.center,

        ))
        page.update()

    def render_place_order():
        # Ensure cart totals are calculated
        recalc_totals()

        main_content.controls.clear()
        main_content.controls.append(ft.Container(
            ft.Column([
                ft.Text("Finalize Order", weight=ft.FontWeight.BOLD,
                        size=28, color=COLORS.RED_700),
                ft.Divider(),
                ft.Text(
                    "You are successfully logged in and ready to complete your purchase.", color=COLORS.GREY_700),

                # Simulated Shipping/Payment Summary
                ft.Container(
                    ft.Column([
                        ft.Text("Shipping Details:",
                                weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Address: 123 Flet St, City, Country (Simulated)"),
                        ft.Divider(height=5),
                        ft.Text("Payment Method:", weight=ft.FontWeight.BOLD),
                        ft.Text("Visa **** 4242 (Simulated)"),
                    ], spacing=6),
                    padding=15,
                    bgcolor=COLORS.BLUE_50,
                    border_radius=8,
                    border=ft.border.all(1, COLORS.BLUE_200)
                ),

                ft.Divider(),

                # Total Summary
                ft.Column([
                    subtotal_txt,
                    shipping_txt,
                    ft.Divider(thickness=2),
                    total_txt,
                ], spacing=5),

                ft.Container(height=10),

                ft.ElevatedButton(
                    "Place Order Now",
                    icon=ft.Icons.SHOPPING_CART_CHECKOUT,
                    on_click=handle_place_order,
                    disabled=len(cart) == 0,  # Disable if cart is empty
                    style=ft.ButtonStyle(
                        bgcolor=COLORS.RED_600, color=COLORS.WHITE, padding=20
                    )
                ),

                ft.TextButton("Cancel and Return to Cart",
                              on_click=lambda e: render_order_review())

            ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.START),
            padding=40,
            bgcolor=COLORS.WHITE,
            border_radius=10,
            width=500,  # Constrain width for a better form look
            alignment=ft.alignment.center
        ))
        page.update()

    def render_order_confirmation(final_total_charged_str: str):
        """Renders the order confirmation screen using the captured total."""
        main_content.controls.clear()
        main_content.controls.append(ft.Container(
            ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE,
                        size=60, color=COLORS.GREEN_600),
                ft.Text("Order Successfully Placed!",
                        weight=ft.FontWeight.BOLD, size=28, color=COLORS.GREEN_700),
                ft.Text(
                    "Your order #12345 has been confirmed and will be shipped soon.", color=COLORS.GREY_700),
                ft.Divider(),
                # --- FIXED: Use the passed string instead of the reset global control ---
                ft.Text(
                    f"Total Charged: {final_total_charged_str}", weight=ft.FontWeight.BOLD, size=18),
                # ------------------------------------------------------------------------
                ft.Container(height=20),
                ft.ElevatedButton("Back to Shopping", on_click=lambda e: render_home(),
                                  style=ft.ButtonStyle(bgcolor=COLORS.BLUE_400, color=COLORS.WHITE)),
                ft.TextButton("View Past Orders (Simulated)", on_click=lambda e: show_message(
                    "Past orders feature not implemented.", COLORS.BLUE_400))
            ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40,
            bgcolor=COLORS.WHITE,
            border_radius=10,
            width=500,
            alignment=ft.alignment.center
        ))
        page.update()

    def render_contact():
        main_content.controls.clear()
        main_content.controls.append(ft.Container(
            ft.Column([
                ft.Text("Contact Us", weight=ft.FontWeight.BOLD, size=24),
                ft.Divider(),
                ft.Text("Email: support@emajohn.com"),
                ft.Text("Phone: +1 (555) EMA-JOHN"),
                ft.TextField(label="Your Name"),
                ft.TextField(label="Your Email"),
                ft.TextField(label="Your Message",
                             multiline=True, min_lines=3),
                ft.ElevatedButton(
                    "Send Message",
                    style=ft.ButtonStyle(
                        bgcolor=COLORS.BLUE_400, color=COLORS.WHITE),
                    on_click=lambda e: show_message("Message sent! Thank you.", COLORS.BLUE_400))
            ], spacing=12),
            padding=20,
            bgcolor=COLORS.WHITE,
            border_radius=10,
        ))
        page.update()

    def render_about():
        main_content.controls.clear()
        main_content.controls.append(ft.Container(
            ft.Column([
                ft.Text("About EMA-John", weight=ft.FontWeight.BOLD, size=24),
                ft.Divider(),
                ft.Text("EMA-John is a conceptual e-commerce platform built as a demonstration of responsive design capabilities using the Flet framework."),
                ft.Text("Our goal is to deliver a seamless shopping experience that adapts perfectly to any device size, from mobile phones to large desktop screens."),
                ft.Text(
                    "Technologies used: Flet for UI, Python for logic, and a cloud-hosted JSON file for product data."),
            ], spacing=10),
            padding=20,
            bgcolor=COLORS.WHITE,
            border_radius=10,
        ))
        page.update()

    # Top area (Header, Navigation, Search/Sort)
    top_area = ft.Column(
        [
            # Header Row
            ft.ResponsiveRow(
                [
                    ft.Container(
                        content=ft.Image(
                            src="./assets/logo.png",
                            expand=True,
                            fit=ft.ImageFit.CONTAIN,
                        ),
                        col={"md": 4, "sm": 12},
                        alignment=ft.alignment.center_left,
                        padding=ft.padding.only(left=10)
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),

            # Navbar
            ft.ResponsiveRow(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Row(  # Nav Links
                                    [
                                        ft.TextButton(
                                            "Home", on_click=lambda e: render_home()),
                                        ft.TextButton(
                                            "Order Review", on_click=lambda e: render_order_review()),
                                        ft.TextButton(
                                            "About", on_click=lambda e: render_about()),
                                        ft.TextButton(
                                            "Contact", on_click=lambda e: render_contact()),
                                    ],
                                    wrap=True,
                                    spacing=6,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),

                                ft.Row(  # Cart and Sign In
                                    [
                                        ft.Row(
                                            [
                                                ft.IconButton(
                                                    icon=ft.Icons.SHOPPING_CART,
                                                    tooltip="Cart",
                                                    icon_color="#d84814",
                                                    on_click=lambda e: render_order_review()  # Link to cart view
                                                ),
                                                ft.Container(
                                                    content=cart_count_txt, padding=ft.padding.only(bottom=5)),
                                            ],
                                            spacing=2,
                                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        ),
                                        # Use the dynamic sign_in_btn control
                                        sign_in_btn,
                                    ],
                                    spacing=12,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            expand=True,
                        ),
                        padding=ft.padding.symmetric(
                            vertical=6, horizontal=12),
                        col={"sm": 12},
                        bgcolor=COLORS.WHITE,
                    )
                ],
                run_spacing=6,
                spacing=6,
            ),

            # Search Bar & Sort Dropdown
            ft.ResponsiveRow(
                [search_input, sort_dropdown],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                run_spacing=12,
            ),
            ft.Divider(thickness=1, color=COLORS.GREY_300, height=20),
        ], spacing=0  # Remove extra spacing from column
    )

    # Build ResponsiveRow layout (products | cart)
    def build_responsive_layout():
        # Populate product row and cart list view
        refresh_cart_ui()
        # NOTE: Initial product rendering is handled by the first call to on_search_or_sort below

        # Product Column Setup
        products_column.controls.clear()
        products_column.controls.append(ft.Row([
            ft.Text("All Products", weight=ft.FontWeight.BOLD, size=20),
            # FIXED: Use the dynamic product_count_txt control
            product_count_txt],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        products_column.controls.append(ft.Divider())
        # products_row contains the responsive grid of product cards
        products_column.controls.append(products_row)

        # Cart Column Setup
        cart_column.controls.clear()
        cart_column.controls.append(
            ft.Text("Your Cart", weight=ft.FontWeight.BOLD, size=20))
        cart_column.controls.append(ft.Divider())
        cart_column.controls.append(cart_listview)
        cart_column.controls.append(ft.Divider())
        cart_column.controls.append(subtotal_txt)
        cart_column.controls.append(shipping_txt)
        cart_column.controls.append(total_txt)
        # Updated Checkout button to trigger the login check
        cart_column.controls.append(ft.ElevatedButton(
            "Checkout", on_click=navigate_to_checkout,
            style=ft.ButtonStyle(bgcolor=COLORS.RED_700, color=COLORS.WHITE)))

        # Outer ResponsiveRow container
        rr = ft.ResponsiveRow([
            ft.Container(products_column, padding=12, bgcolor=COLORS.WHITE, border_radius=10, col={
                         # Products: 12 (sm) or 8/9 (md/xl)
                         "sm": 12, "md": 8, "xl": 9}, expand=True),
            ft.Container(cart_column, padding=12, bgcolor=COLORS.WHITE, border_radius=10, col={
                         # Cart: 12 (sm) or 4/3 (md/xl)
                         "sm": 12, "md": 4, "xl": 3}, expand=True),
        ], run_spacing=15, spacing=15, expand=True)
        return rr

    # Search / sort handlers
    def on_search_or_sort(e=None):
        q = search_input.value.strip().lower()
        filtered = [p for p in products if (q in p["name"].lower() or q in p.get(
            "category", "").lower())] if q else products.copy()

        sort_val = sort_dropdown.value or "Relevance"
        if sort_val == "Price: Low → High":
            filtered.sort(key=lambda x: x["price"])
        elif sort_val == "Price: High → Low":
            filtered.sort(key=lambda x: -x["price"])
        elif sort_val == "Top Rated":
            filtered.sort(
                key=lambda x: (-x.get("ratings", 0), -x.get("ratingsCount", 0)))

        # Update the product count text control with the filtered count
        product_count_txt.value = f"({len(filtered)} items)"

        # Re-render filtered list using the new responsive logic
        render_products(filtered)
        # Note: render_products calls page.update()

    search_input.on_change = on_search_or_sort
    sort_dropdown.on_change = on_search_or_sort

    # Layout builder function (handles initial load and resize)
    def layout_builder(e=None):
        # We only update the page controls, the content inside main_content remains
        page.controls.clear()
        page.add(ft.Container(content=top_area,
                              padding=ft.padding.symmetric(horizontal=12)))
        page.add(ft.Container(content=main_content, padding=12, expand=True))

        # When layout changes (resize), we must re-render products to adjust image size
        # This function also updates the product count
        on_search_or_sort()

    page.on_resize = layout_builder

    # Initial render sequence
    page.add(ft.Container(content=top_area,
                          padding=ft.padding.symmetric(horizontal=12)))
    page.add(ft.Container(content=main_content, padding=12, expand=True))
    render_home()
    # Ensure initial UI state for sign in button is correct
    update_sign_in_ui()
    # Call once to render initial product list and set the correct initial count
    on_search_or_sort()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
