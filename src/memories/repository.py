from typing import List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase


class MemoriesRepository:
    """Repository for fetching memory items from tickets collection."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["tickets"]

    async def get_memories_paginated(
        self,
        user_id: str,
        page: int,
        limit: int,
        type_filter: Optional[str] = None,
        title: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[List[str]] = None,
    ) -> Tuple[List[dict], int]:
        """
        Get paginated memory items from tickets.

        Each ticket can produce up to 2 memory items:
        - 1 for ticket image (if exists)
        - 1 for 2-shot image (if exists)

        Args:
            user_id: User's ID
            page: Page number (1-indexed)
            limit: Items per page
            type_filter: 'TICKET', '2SHOT', or None for all

        Returns:
            Tuple of (list of memory items, total count)
        """
        # Use $facet to get both ticket images and 2-shot images separately
        # Then combine them with $unionWith or process separately

        match_conditions = {"user_id": user_id}

        if title:
            match_conditions["event.title"] = title

        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            if date_query:
                match_conditions["event.date"] = date_query

        if days:
            upper_days = [d.upper() for d in days]
            match_conditions["$expr"] = {
                "$in": [{"$toUpper": "$event.day"}, upper_days]
            }

        base_match = {"$match": match_conditions}

        # Pipeline for ticket images
        ticket_pipeline = [
            base_match,
            {"$match": {"imageUrl": {"$exists": True, "$ne": None, "$ne": ""}}},
            {
                "$project": {
                    "_id": 0,
                    "type": {"$literal": "TICKET"},
                    "imageUrl": "$imageUrl",
                    "ticketId": {"$toString": "$_id"},
                    "date": "$event.date",
                    "time": "$event.time",
                    "title": "$event.title",
                    "seatSection": "$seat.section",
                    "seatNumber": {"$toString": "$seat.number"},
                    "notes": "$notes",
                    "blurHash": "$blurHash",
                    "eventTitle": "$event.title",
                    "twoShotMemberName": {"$literal": None},
                    "twoShotType": {"$literal": None},
                }
            },
        ]

        # Pipeline for 2-shot images
        twoshot_pipeline = [
            base_match,
            {
                "$match": {
                    "two_shot.imageUrl": {"$exists": True, "$ne": None, "$ne": ""}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "type": {"$literal": "2SHOT"},
                    "imageUrl": "$two_shot.imageUrl",
                    "ticketId": {"$toString": "$_id"},
                    "date": "$event.date",
                    "time": "$event.time",
                    "title": {
                        "$concat": [
                            "2-Shot: ",
                            {"$ifNull": ["$two_shot.member_name", "Unknown"]},
                        ]
                    },
                    "seatSection": {"$literal": None},
                    "seatNumber": {"$literal": None},
                    "notes": "$notes",
                    "blurHash": "$two_shot.blurHash",
                    "eventTitle": "$event.title",
                    "twoShotMemberName": "$two_shot.member_name",
                    "twoShotType": "$two_shot.type",
                }
            },
        ]

        # Apply type filter
        if type_filter == "TICKET":
            # Only get ticket images
            pipeline = ticket_pipeline
        elif type_filter == "2SHOT":
            # Only get 2-shot images
            pipeline = twoshot_pipeline
        else:
            # Get both and union them using $facet
            pipeline = [
                base_match,
                {
                    "$facet": {
                        "tickets": [
                            {
                                "$match": {
                                    "imageUrl": {
                                        "$exists": True,
                                        "$ne": None,
                                        "$ne": "",
                                    }
                                }
                            },
                            {
                                "$project": {
                                    "_id": 0,
                                    "type": {"$literal": "TICKET"},
                                    "imageUrl": "$imageUrl",
                                    "ticketId": {"$toString": "$_id"},
                                    "date": "$event.date",
                                    "time": "$event.time",
                                    "title": "$event.title",
                                    "seatSection": "$seat.section",
                                    "seatNumber": {"$toString": "$seat.number"},
                                    "notes": "$notes",
                                    "blurHash": "$blurHash",
                                    "eventTitle": "$event.title",
                                    "twoShotMemberName": {"$literal": None},
                                    "twoShotType": {"$literal": None},
                                }
                            },
                        ],
                        "twoshots": [
                            {
                                "$match": {
                                    "two_shot.imageUrl": {
                                        "$exists": True,
                                        "$ne": None,
                                        "$ne": "",
                                    }
                                }
                            },
                            {
                                "$project": {
                                    "_id": 0,
                                    "type": {"$literal": "2SHOT"},
                                    "imageUrl": "$two_shot.imageUrl",
                                    "ticketId": {"$toString": "$_id"},
                                    "date": "$event.date",
                                    "time": "$event.time",
                                    "title": {
                                        "$concat": [
                                            "2-Shot: ",
                                            {
                                                "$ifNull": [
                                                    "$two_shot.member_name",
                                                    "Unknown",
                                                ]
                                            },
                                        ]
                                    },
                                    "seatSection": {"$literal": None},
                                    "seatNumber": {"$literal": None},
                                    "notes": "$notes",
                                    "blurHash": "$two_shot.blurHash",
                                    "eventTitle": "$event.title",
                                    "twoShotMemberName": "$two_shot.member_name",
                                    "twoShotType": "$two_shot.type",
                                }
                            },
                        ],
                    }
                },
                # Combine both arrays
                {
                    "$project": {
                        "combined": {"$concatArrays": ["$tickets", "$twoshots"]}
                    }
                },
                # Unwind the combined array
                {"$unwind": "$combined"},
                # Replace root with item
                {"$replaceRoot": {"newRoot": "$combined"}},
            ]

        # For filtered queries, just extend the pipeline
        if type_filter in ["TICKET", "2SHOT"]:
            # Get total count first
            count_pipeline = pipeline.copy()
            count_pipeline.append({"$count": "total"})
            count_result = await self.collection.aggregate(count_pipeline).to_list(
                length=1
            )
            total_count = count_result[0]["total"] if count_result else 0

            # Add sorting and pagination
            skip = (page - 1) * limit
            pipeline.extend(
                [
                    {"$sort": {"date": -1, "time": -1}},
                    {"$skip": skip},
                    {"$limit": limit},
                ]
            )

            results = await self.collection.aggregate(pipeline).to_list(length=None)
            return results, total_count
        else:
            # For ALL filter with facet, we need different counting
            count_pipeline = [
                base_match,
                {
                    "$facet": {
                        "ticketCount": [
                            {
                                "$match": {
                                    "imageUrl": {
                                        "$exists": True,
                                        "$ne": None,
                                        "$ne": "",
                                    }
                                }
                            },
                            {"$count": "count"},
                        ],
                        "twoshotCount": [
                            {
                                "$match": {
                                    "two_shot.imageUrl": {
                                        "$exists": True,
                                        "$ne": None,
                                        "$ne": "",
                                    }
                                }
                            },
                            {"$count": "count"},
                        ],
                    }
                },
            ]
            count_result = await self.collection.aggregate(count_pipeline).to_list(
                length=1
            )

            ticket_count = (
                count_result[0]["ticketCount"][0]["count"]
                if count_result and count_result[0]["ticketCount"]
                else 0
            )
            twoshot_count = (
                count_result[0]["twoshotCount"][0]["count"]
                if count_result and count_result[0]["twoshotCount"]
                else 0
            )
            total_count = ticket_count + twoshot_count

            # Add sorting and pagination
            skip = (page - 1) * limit
            pipeline.extend(
                [
                    {"$sort": {"date": -1, "time": -1}},
                    {"$skip": skip},
                    {"$limit": limit},
                ]
            )

            results = await self.collection.aggregate(pipeline).to_list(length=None)
            return results, total_count

    async def get_top_two_shot_stats(
        self,
        user_id: str,
        year: Optional[int] = None,
        start_month: int = 0,
        end_month: int = 11,
        is_all_data: bool = True,
    ) -> dict:
        """
        Calculate Top 2-Shot stats using aggregation.
        """
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "two_shot.member_name": {"$exists": True, "$ne": None, "$ne": ""},
                }
            }
        ]

        if not is_all_data and year is not None:
            pipeline.extend(
                [
                    {
                        "$match": {
                            "event.date": {
                                "$exists": True,
                                "$type": "string",
                                "$regex": r"^\d{4}-\d{2}-\d{2}",
                            }
                        }
                    },
                    {
                        "$addFields": {
                            "parsedDate": {
                                "$dateFromString": {
                                    "dateString": "$event.date",
                                    "format": "%Y-%m-%d",
                                }
                            }
                        }
                    },
                    {
                        "$addFields": {
                            "year": {"$year": "$parsedDate"},
                            "month": {"$month": "$parsedDate"},
                        }
                    },
                    {
                        "$match": {
                            "year": year,
                            "month": {"$gte": start_month + 1, "$lte": end_month + 1},
                        }
                    },
                    {"$project": {"parsedDate": 0, "year": 0, "month": 0}},
                ]
            )

        pipeline.extend(
            [
                {
                    "$facet": {
                        "ranking": [
                            # Sort descending inside the facet before grouping to guarantee $first picks the newest
                            {"$sort": {"event.date": -1}},
                            {
                                "$group": {
                                    "_id": {
                                        "$trim": {"input": "$two_shot.member_name"}
                                    },
                                    "count": {"$sum": 1},
                                    "spend": {"$sum": "$two_shot.price"},
                                    "lastDate": {"$first": "$event.date"},
                                    "image": {"$first": "$two_shot.imageUrl"},
                                    "blurHash": {"$first": "$two_shot.blurHash"},
                                }
                            },
                            {
                                "$project": {
                                    "_id": 0,
                                    "name": "$_id",
                                    "count": 1,
                                    "spend": 1,
                                    "lastDate": 1,
                                    "image": 1,
                                    "blurHash": 1,
                                }
                            },
                            {"$sort": {"count": -1, "spend": -1, "lastDate": -1}},
                        ],
                        "totals": [
                            {
                                "$group": {
                                    "_id": None,
                                    "totalSpend": {"$sum": "$two_shot.price"},
                                    "totalCount": {"$sum": 1},
                                }
                            }
                        ],
                    }
                },
            ]
        )

        result = await self.collection.aggregate(pipeline).to_list(length=1)

        if not result:
            return {"ranking": [], "totalTwoShotSpend": 0, "totalTwoShotCount": 0}

        data = result[0]
        totals = data.get("totals", [])
        total_data = totals[0] if totals else {"totalSpend": 0, "totalCount": 0}

        return {
            "ranking": data.get("ranking", []),
            "totalTwoShotSpend": total_data.get("totalSpend", 0),
            "totalTwoShotCount": total_data.get("totalCount", 0),
        }
