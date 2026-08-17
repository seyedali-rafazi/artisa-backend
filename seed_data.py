"""Database Seeder Script for Artisa API."""

import asyncio
from datetime import timedelta
from passlib.context import CryptContext

from core.database import db
from core.timezone import now_utc
from models.user import User
from models.product import Product
from models.comment import Comment
from models.address import Address
from models.order import Order, OrderItem, ShippingAddress
from models.blog import Article
from models.faq import FAQ
from models.banner import Banner
from models.special_offer import SpecialOffer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed():
    print("Connecting to database...")
    await db.connect_db()

    # Clear existing collections
    print("Clearing existing data...")
    await User.delete_all()
    await Product.delete_all()
    await Comment.delete_all()
    await Address.delete_all()
    await Order.delete_all()
    await Article.delete_all()
    await FAQ.delete_all()
    await Banner.delete_all()
    await SpecialOffer.delete_all()

    # Seed Admin User & Demo User
    print("Seeding Users...")
    demo_user = User(
        name="کاربر نمونه",
        email="user@artisa.com",
        hashed_password=pwd_context.hash("123456"),
        phone="09121234567",
        role="کاربر عادی",
    )
    await demo_user.insert()

    admin_user = User(
        name="مدیر سیستم",
        email="admin@artisa.com",
        hashed_password=pwd_context.hash("admin123"),
        phone="09120000000",
        role="مدیر سیستم",
        is_superuser=True,
    )
    await admin_user.insert()

    # Seed Products
    print("Seeding Products...")
    products_data = [
        {
            "name": "تابلو نقاشی رنگ‌روغن «افق طلایی»",
            "nameEn": "Golden Horizon Oil Painting",
            "price": 3200000,
            "oldPrice": 4500000,
            "image": "https://images.unsplash.com/photo-1578301978693-85fa9c0320b9?auto=format&fit=crop&w=400&q=80",
            "category": "تابلو نقاشی",
            "categoryEn": "Painting",
            "rating": 4.9,
            "isSpecial": True,
            "isBestSeller": False,
            "description": "تابلو رنگ‌روغن دست‌ساز با تکنیک پالت‌نایف روی بوم کتان ایتالیایی. اثر اورجینال با گواهی اصالت و امضای هنرمند. ابعاد ۸۰ در ۶۰ سانتی‌متر.",
            "descriptionEn": "Handmade oil painting with palette knife technique on Italian linen canvas.",
            "specifications": {
                "تکنیک": "رنگ‌روغن روی بوم کتان",
                "ابعاد": "۸۰ × ۶۰ سانتی‌متر",
                "هنرمند": "نیلوفر حسینی",
                "سبک": "امپرسیونیسم مدرن",
                "گواهی اصالت": "دارد",
            },
        },
        {
            "name": "تابلو آبرنگ «باغ در سپیده‌دم»",
            "nameEn": "Garden at Dawn Watercolor",
            "price": 1850000,
            "oldPrice": 2400000,
            "image": "https://images.unsplash.com/photo-1549887534-1541e9326642?auto=format&fit=crop&w=400&q=80",
            "category": "تابلو نقاشی",
            "categoryEn": "Painting",
            "rating": 4.7,
            "isSpecial": False,
            "isBestSeller": True,
            "description": "نقاشی آبرنگ ظریف با دیدگاه باغ سنتی ایرانی در لحظه طلوع آفتاب. چاپ باکیفیت آرت‌پرینت روی کاغذ ۳۰۰ گرمی ضدآب.",
            "descriptionEn": "Delicate watercolor painting of a traditional Iranian garden at sunrise.",
            "specifications": {
                "تکنیک": "آبرنگ — آرت‌پرینت",
                "ابعاد": "۵۰ × ۷۰ سانتی‌متر",
                "نوع کاغذ": "۳۰۰ گرمی ضدآب",
                "هنرمند": "سارا رحیمی",
            },
        },
        {
            "name": "دیوارکوب ماکرامه گره‌دار بوهو",
            "nameEn": "Boho Macrame Wall Hanging",
            "price": 680000,
            "image": "https://images.unsplash.com/photo-1611486212557-88be5ff6f941?auto=format&fit=crop&w=400&q=80",
            "category": "هنر دیواری",
            "categoryEn": "Wall Art",
            "rating": 4.6,
            "isSpecial": True,
            "isBestSeller": False,
            "description": "دیوارکوب دست‌بافت ماکرامه با نخ پنبه طبیعی اکرو و چوب دریفت‌وود طبیعی. ایجادکننده فضای گرم و بوهو در هر اتاق.",
            "descriptionEn": "Hand-woven macrame wall hanging with natural ecru cotton rope.",
            "specifications": {
                "جنس": "نخ پنبه طبیعی اکرو",
                "چوب": "دریفت‌وود طبیعی",
                "ابعاد": "عرض ۴۵ سانتی‌متر، ارتفاع ۸۰ سانتی‌متر",
                "ساخت": "دست‌بافت",
            },
        },
        {
            "name": "پوستر هنری مینیمال «خطوط طلایی»",
            "nameEn": "Minimal Golden Lines Art Poster",
            "price": 320000,
            "oldPrice": 450000,
            "image": "https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?auto=format&fit=crop&w=400&q=80",
            "category": "هنر مدرن",
            "categoryEn": "Modern Art",
            "rating": 4.5,
            "isSpecial": True,
            "isBestSeller": False,
            "description": "پوستر هنری با طراحی گرافیکی مینیمال و خطوط هندسی طلایی روی پس‌زمینه مشکی. چاپ UV روی کاغذ گلاسه ۲۰۰ گرمی.",
            "specifications": {
                "ابعاد": "۴۰ × ۵۰ سانتی‌متر",
                "نوع چاپ": "UV گلاسه",
                "وزن کاغذ": "۲۰۰ گرمی",
            },
        },
        {
            "name": "مجسمه آبستره سرامیکی «موج»",
            "nameEn": "Wave Abstract Ceramic Sculpture",
            "price": 1450000,
            "image": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=400&q=80",
            "category": "مجسمه و دکوری",
            "categoryEn": "Sculpture",
            "rating": 4.8,
            "isSpecial": False,
            "isBestSeller": True,
            "description": "مجسمه کوچک دست‌ساز سرامیکی با لعاب فیروزه‌ای و طراحی انتزاعی الهام‌گرفته از امواج دریا.",
            "specifications": {
                "جنس": "سرامیک لعاب‌دار",
                "ابعاد": "۱۵ × ۸ × ۲۰ سانتی‌متر",
                "ساخت": "کاملاً دست‌ساز",
            },
        },
        {
            "name": "قاب عکس چوبی گالری‌وال ست ۶ تایی",
            "nameEn": "Gallery Wall Wooden Frame Set of 6",
            "price": 1100000,
            "oldPrice": 1400000,
            "image": "https://images.unsplash.com/photo-1513519245088-0e12902e35ca?auto=format&fit=crop&w=400&q=80",
            "category": "قاب و فریم",
            "categoryEn": "Frame",
            "rating": 4.6,
            "isSpecial": False,
            "isBestSeller": True,
            "description": "ست ۶ تایی قاب عکس چوبی با پوشش لاک مات برای چیدمان گالری‌وال روی دیوار.",
            "specifications": {
                "تعداد": "۶ عدد (۳ سایز مختلف)",
                "جنس": "چوب راش طبیعی",
            },
        },
    ]

    inserted_products = []
    for pdata in products_data:
        p = Product(**pdata)
        await p.insert()
        inserted_products.append(p)

    # Seed Comments
    print("Seeding Comments...")
    if inserted_products:
        c1 = Comment(
            productId=str(inserted_products[0].id),
            userName="زهرا رحیمی",
            text="بسیار باکیفیت و زیباست، دقیقا مثل عکسشه. پیشنهاد میکنم بخرید.",
            rating=5,
            date="۱۴۰۵/۰۳/۱۲",
        )
        c2 = Comment(
            productId=str(inserted_products[0].id),
            userName="بابک راد",
            text="بسته‌بندی تخصصی داشت. ارسالش هم سریع و مطمئن بود. ممنون از آرتیسا.",
            rating=4,
            date="۱۴۰۵/۰۳/۱۸",
        )
        await c1.insert()
        await c2.insert()

    # Seed User Address
    print("Seeding Addresses...")
    address = Address(
        userId=str(demo_user.id),
        title="خانه",
        fullName="کاربر نمونه",
        phone="09121234567",
        province="تهران",
        city="تهران",
        postalCode="1234567890",
        addressLine="خیابان ولیعصر، کوچه گلستان، پلاک ۱۲، واحد ۳",
        isDefault=True,
    )
    await address.insert()

    # Seed Orders
    print("Seeding Orders...")
    order1 = Order(
        orderId="ORD-10042",
        userId=str(demo_user.id),
        date="۱۴۰۵/۰۳/۱۵",
        status="delivered",
        totalPrice=5050000,
        paymentStatus="paid",
        paymentMethod="online",
        items=[
            OrderItem(
                id="p1",
                name="تابلو نقاشی رنگ‌روغن «افق طلایی»",
                price=3200000,
                quantity=1,
                image="https://images.unsplash.com/photo-1578301978693-85fa9c0320b9?auto=format&fit=crop&w=400&q=80",
            ),
            OrderItem(
                id="p2",
                name="تابلو آبرنگ «باغ در سپیده‌دم»",
                price=1850000,
                quantity=1,
                image="https://images.unsplash.com/photo-1549887534-1541e9326642?auto=format&fit=crop&w=400&q=80",
            ),
        ],
        shippingAddress=ShippingAddress(
            fullName="کاربر نمونه",
            phone="09121234567",
            postalCode="1234567890",
            address="خیابان ولیعصر، کوچه گلستان، پلاک ۱۲",
        ),
    )
    await order1.insert()

    order2 = Order(
        orderId="ORD-10038",
        userId=str(demo_user.id),
        date="۱۴۰۵/۰۲/۲۸",
        status="shipped",
        totalPrice=680000,
        paymentStatus="paid",
        paymentMethod="online",
        items=[
            OrderItem(
                id="p3",
                name="دیوارکوب ماکرامه گره‌دار بوهو",
                price=680000,
                quantity=1,
                image="https://images.unsplash.com/photo-1611486212557-88be5ff6f941?auto=format&fit=crop&w=400&q=80",
            ),
        ],
    )
    await order2.insert()

    # Seed Articles
    print("Seeding Articles...")
    articles = [
        Article(
            articleId="a1",
            title="راهنمای کامل چیدمان گالری‌وال در منزل",
            desc="گالری‌وال یا دیوار گالری یکی از جذاب‌ترین روش‌های دکوراسیون دیواری است. در این مقاله نحوه انتخاب آثار، ترکیب قاب‌ها، فاصله‌گذاری مناسب و چیدمان ایده‌آل برای انواع دیوارها را بررسی می‌کنیم.",
            date="۱۴۰۵/۰۴/۱۵",
            author="آرتا نظری",
            image="https://images.unsplash.com/photo-1513519245088-0e12902e35ca?auto=format&fit=crop&w=400&q=80",
        ),
        Article(
            articleId="a2",
            title="تفاوت تابلو اورجینال و رپرودکشن: کدام برای شما مناسب است؟",
            desc="خرید تابلو نقاشی اورجینال یا چاپ با کیفیت؟ در این مقاله مزایا، معایب، تفاوت قیمت و نحوه تشخیص هر دو گزینه را به‌صورت کامل بررسی می‌کنیم.",
            date="۱۴۰۵/۰۴/۱۰",
            author="سارا رحیمی",
            image="https://images.unsplash.com/photo-1578301978693-85fa9c0320b9?auto=format&fit=crop&w=400&q=80",
        ),
    ]
    for art in articles:
        await art.insert()

    # Seed FAQs
    print("Seeding FAQs...")
    faqs = [
        FAQ(
            question="آثار هنری فروشگاه آرتیسا اورجینال هستند؟",
            answer="بله، تمام تابلوهای نقاشی با برچسب «اورجینال» دارای گواهی اصالت (Certificate of Authenticity) با امضای هنرمند هستند.",
            order=1,
        ),
        FAQ(
            question="آثار هنری چطور بسته‌بندی و ارسال می‌شوند؟",
            answer="تمام آثار هنری با استانداردهای گالری‌داری بسته‌بندی می‌شوند. ارسال به سراسر ایران با پیک اختصاصی یا پست پیشتاز انجام می‌شود.",
            order=2,
        ),
    ]
    for f in faqs:
        await f.insert()

    # Seed Banners
    print("Seeding Banners...")
    banner1 = Banner(
        title="گالری آثار هنری اورجینال",
        subtitle="مجموعه‌ای بی‌نظیر از تابلوهای نقاشی، دیوارکوب‌های دست‌ساز و مجسمه‌های دکوراتیو",
        badge="تخفیف ویژه جشنواره تابستانه",
        buttonText="مشاهده محصولات",
        image="https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=1200&q=80",
        order=1,
    )
    await banner1.insert()

    # Seed Special Offers
    print("Seeding Special Offers...")
    special_products = await Product.find({"isSpecial": True}).to_list()
    special_product_ids = [str(p.id) for p in special_products] if special_products else []

    if not special_product_ids:
        all_prods = await Product.find().limit(4).to_list()
        special_product_ids = [str(p.id) for p in all_prods]

    demo_offer = SpecialOffer(
        title="جشنواره شگفت‌انگیز آثار منتخب",
        description="تخفیف استثنایی تا ۴۰٪ روی پرطرفدارترین تابلوها و آثار هنری دست‌ساز برای مدت محدود",
        product_ids=special_product_ids,
        start_at=now_utc() - timedelta(hours=2),
        end_at=now_utc() + timedelta(days=5, hours=14, minutes=30),
        is_active=True,
    )
    await demo_offer.insert()

    print("Database successfully seeded!")
    await db.close_db()


if __name__ == "__main__":
    asyncio.run(seed())
