# Data dictionary

All dates are ISO `YYYY-MM-DD`. Read them with `parse_dates=["date"]`. Numeric CSV values use a decimal point; amounts are EUR. There are no intentionally blank cells.

## sales.csv

| Column | Type | Definition |
| --- | --- | --- |
| date | date | Sale day |
| product_id | string | P01 Coffee, P02 Tea, P03 Sandwich, P04 Snack, P05 Lunch meal |
| product_name | string | Readable product name |
| category | string | Drink, Food or Snack; used to group related products |
| quantity_sold | integer | Units sold during that day |
| unit_price | decimal | Actual per-unit price after any promotion, in EUR |
| revenue | decimal | quantity_sold × unit_price, in EUR |

Primary key: date + product_id. Nonnegative quantities, positive prices; prices and revenue have two decimal places.

## weather.csv

| Column | Type | Definition |
| --- | --- | --- |
| date | date | Observation day, unique |
| temperature_c | float | Synthetic daily temperature in degrees Celsius |
| rainfall_mm | float | Synthetic rainfall in millimetres; nonnegative |
| weather_condition | string | rainy when rainfall > 0; otherwise cold when temperature < 5°C, or dry |

## academic_calendar.csv

| Column | Type | Definition |
| --- | --- | --- |
| date | date | Calendar day, unique |
| day_of_week | string | English weekday matching date |
| is_lecture_day | boolean | True on non-holiday weekdays in this fictional calendar |
| is_exam_period | boolean | Whether the day is in the designed exam window |
| is_holiday | boolean | Explicit fictional holiday flag; weekends are not automatically holidays |
| academic_period | string | teaching, exams or holiday; holiday takes precedence |

A lecture-day flag can overlap the exam-period flag by design. It means the campus is in its usual weekday operating pattern, not that every class actually met.

## campus_events.csv

| Column | Type | Definition |
| --- | --- | --- |
| event_id | string | Unique event identifier |
| date | date | Event day; references the shared calendar |
| event_name | string | Fictional event name |
| event_type | string | campus_event |
| expected_attendance | integer | Planned attendees, not actual café visits |

There is at most one generated event per date in this version. Event information alone does not establish an effect on sales.

## promotions.csv

| Column | Type | Definition |
| --- | --- | --- |
| promotion_id | string | Unique promotion identifier |
| date | date | Promotion day |
| product_id | string | Product receiving the promotion; references sales |
| promotion_type | string | price_discount |
| discount_percent | integer | Discount from the regular price; actual price already stored in sales |

Primary key: date + product_id. Promotion IDs are unique. Dates without a record have no generated promotion.
