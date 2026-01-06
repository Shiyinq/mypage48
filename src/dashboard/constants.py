class DashboardConstants:
    """Constants used in Dashboard Service."""

    # Days of the week for day preference statistics
    DAYS = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]

    # Theater rows for seat statistics
    THEATER_ROWS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]

    # Show images mapping for top show card
    # These URLs are copied from frontend/src/lib/constants/shows.ts
    SHOW_IMAGES = [
        {
            "title": "Pertaruhan Cinta",
            "image": "https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1760105446/wwiaxahqs3ti0lhqdszz.jpg",
        },
        {
            "title": "Pajama Drive",
            "image": "https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1717174034/xspjxcs9wwm9jxwhiy5q.jpg",
        },
        {
            "title": "Aturan Anti Cinta",
            "image": "https://cdn.idntimes.com/content-images/post/20251115/50a27780-93e7-4e40-8474-60f6e0cca6da-251115200115.jpg",
        },
        {
            "title": "Sambil Menggandeng Erat Tanganku",
            "image": "https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1743898507/nvw4gqjtdhje2ftxt9i1.jpg",
        },
        {
            "title": "Cara Meminum Ramune",
            "image": "https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1702404446/nixg3rixpjpom3xa0ivf.jpg",
        },
        {
            "title": "Ingin Bertemu",
            "image": "https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1697224788/uploads/w2zvghwk8tocey8e8xhv.jpg",
        },
        {
            "title": "KIRA KIRA GIRLS",
            "image": "https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1763233779/tanfbrrf8oexxmmfoouh.jpg",
        },
        {
            "title": "Tunas di Balik Seragam",
            "image": "https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1698750703/uploads/yvryrdy47ppla0nidn3m.webp",
        },
    ]


class Info:
    """Informational messages."""

    STATS_FETCHED = "Dashboard statistics fetched successfully."


class ErrorCode:
    """Error codes for HTTP exceptions."""

    STATS_FETCH_ERROR = "Failed to fetch dashboard statistics."


class DomainErrorCode:
    """Error codes for Domain exceptions."""

    STATS_FETCH_FAILED = "Failed to fetch dashboard statistics."
