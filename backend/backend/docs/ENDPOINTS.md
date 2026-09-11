# Main API endpoints

Authentication
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me

Farmer/Farm
- POST /api/farms
- GET /api/farms

Resources
- POST /api/resources
- GET /api/resources
- PATCH /api/resources/{id}/status

Resource allocation
- POST /api/requests
- GET /api/requests
- GET /api/requests/{id}
- POST /api/scheduling/allocate/{request_id}
- POST /api/scheduling/confirm/{request_id}
- GET /api/scheduling/calendar

Disruptions
- POST /api/disruptions

Weather
- GET /api/weather

AI
- POST /api/ml/fertilizer/recommend
- POST /api/ml/pesticide/recommend
- GET /api/ml/fertilizer/history
- GET /api/ml/pesticide/history

Soil image
- POST /api/soil/image-analysis

Labour
- POST /api/labour/providers
- GET /api/labour/providers
- POST /api/labour/requests
- POST /api/labour/offers
- POST /api/labour/offers/{id}/accept

Yield marketplace
- POST /api/market/orders
- GET /api/market/orders
- GET /api/market/orders/matches
- POST /api/market/orders/{id}/respond

Offline
- POST /api/offline/sync

Notifications
- GET /api/notifications
- POST /api/notifications/{id}/read

Master dashboard
- GET /api/dashboard/summary
- GET /api/dashboard/priority-queue
