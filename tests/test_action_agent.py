import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from src.agents.action_agent import ActionAgent

@pytest.fixture
def mock_wcapi():
    return Mock()

@pytest.fixture
def action_agent(mock_wcapi):
    agent = ActionAgent()
    agent.wcapi = mock_wcapi
    return agent

class TestShippingManagement:
    def test_create_shipping_zone(self, action_agent, mock_wcapi):
        # הגדרת נתוני בדיקה
        zone_data = {
            "name": "מרכז הארץ",
            "regions": ["תל אביב", "רמת גן", "גבעתיים"],
            "price": 25.90
        }
        
        # הגדרת תגובת ה-API
        mock_wcapi.post.return_value.status_code = 201
        mock_wcapi.post.return_value.json.return_value = {
            "id": 1,
            "name": zone_data["name"],
            "locations": zone_data["regions"]
        }
        
        # הרצת הפונקציה
        result = action_agent.create_shipping_zone(zone_data)
        
        # בדיקות
        assert "אזור המשלוח" in result and "נוצר בהצלחה" in result
        mock_wcapi.post.assert_called_once_with("shipping/zones", zone_data)

    def test_update_shipping_zone(self, action_agent, mock_wcapi):
        # הגדרת נתוני בדיקה
        zone_id = 1
        update_data = {
            "name": "מרכז מורחב",
            "regions": ["תל אביב", "רמת גן", "גבעתיים", "חולון"],
            "price": 29.90
        }
        
        # הגדרת תגובת ה-API
        mock_wcapi.put.return_value.status_code = 200
        mock_wcapi.put.return_value.json.return_value = {
            "id": zone_id,
            "name": update_data["name"],
            "locations": update_data["regions"]
        }
        
        # הרצת הפונקציה
        result = action_agent.update_shipping_zone(zone_id, update_data)
        
        # בדיקות
        assert "אזור המשלוח" in result and "עודכן בהצלחה" in result
        mock_wcapi.put.assert_called_once_with(f"shipping/zones/{zone_id}", update_data)

    def test_create_shipping_label(self, action_agent, mock_wcapi):
        # הגדרת נתוני בדיקה
        order_id = 123
        label_data = {
            "carrier": "חברת שליחויות",
            "service": "משלוח מהיר"
        }
        
        # הגדרת תגובת ה-API
        mock_wcapi.get.return_value.json.return_value = {
            "id": order_id,
            "shipping_address": {
                "first_name": "ישראל",
                "last_name": "ישראלי",
                "address_1": "רחוב הרצל 1",
                "city": "תל אביב",
                "postcode": "6120101"
            }
        }
        mock_wcapi.post.return_value.status_code = 201
        mock_wcapi.post.return_value.json.return_value = {
            "label_url": "https://example.com/label.pdf"
        }
        
        # הרצת הפונקציה
        result = action_agent.create_shipping_label(order_id, **label_data)
        
        # בדיקות
        assert "נוצרה תווית משלוח" in result
        assert "https://example.com/label.pdf" in result
        mock_wcapi.get.assert_called_once_with(f"orders/{order_id}")
        mock_wcapi.post.assert_called_once()

    def test_track_shipment(self, action_agent, mock_wcapi):
        # הגדרת נתוני בדיקה
        order_id = 123
        
        # הגדרת תגובת ה-API
        mock_wcapi.get.return_value.json.return_value = {
            "id": order_id,
            "shipping_lines": [{
                "tracking_number": "1234567890",
                "method_title": "חברת שליחויות"
            }]
        }
        
        # הרצת הפונקציה
        result = action_agent.track_shipment(order_id)
        
        # בדיקות
        assert "מספר מעקב: 1234567890" in result
        mock_wcapi.get.assert_called_once_with(f"orders/{order_id}")

class TestPaymentManagement:
    def test_add_payment_method(self, action_agent, mock_wcapi):
        # הגדרת נתוני בדיקה
        method_data = {
            "title": "העברה בנקאית",
            "description": "תשלום באמצעות העברה בנקאית",
            "enabled": True
        }
        
        # הגדרת תגובת ה-API
        mock_wcapi.post.return_value.status_code = 201
        mock_wcapi.post.return_value.json.return_value = {
            "id": "bacs",
            "title": method_data["title"],
            "description": method_data["description"],
            "enabled": method_data["enabled"]
        }
        
        # הרצת הפונקציה
        result = action_agent.add_payment_method(method_data)
        
        # בדיקות
        assert "נוספה שיטת תשלום חדשה" in result
        mock_wcapi.post.assert_called_once_with("payment_gateways", method_data)

    def test_process_payment(self, action_agent, mock_wcapi):
        # הגדרת נתוני בדיקה
        order_id = 123
        payment_data = {
            "method": "bacs",
            "method_title": "העברה בנקאית",
            "amount": 199.90
        }
        
        # הגדרת תגובת ה-API
        mock_wcapi.get.return_value.json.return_value = {
            "id": order_id,
            "total": "199.90",
            "status": "pending"
        }
        mock_wcapi.put.return_value.status_code = 200
        mock_wcapi.put.return_value.json.return_value = {
            "id": order_id,
            "status": "processing"
        }
        
        # הרצת הפונקציה
        result = action_agent.process_payment(order_id, payment_data)
        
        # בדיקות
        assert "התשלום עובד בהצלחה" in result
        mock_wcapi.get.assert_called_once_with(f"orders/{order_id}")
        mock_wcapi.put.assert_called_once()

    def test_refund_payment(self, action_agent, mock_wcapi):
        # הגדרת נתוני בדיקה
        order_id = 123
        refund_data = {
            "amount": 50.00,
            "reason": "פגם במוצר"
        }
        
        # הגדרת תגובת ה-API
        mock_wcapi.get.return_value.json.return_value = {
            "id": order_id,
            "total": "199.90",
            "status": "processing"
        }
        mock_wcapi.post.return_value.status_code = 201
        mock_wcapi.post.return_value.json.return_value = {
            "id": 1,
            "amount": "50.00"
        }
        
        # הרצת הפונקציה
        result = action_agent.refund_payment(order_id, refund_data)
        
        # בדיקות
        assert "ההחזר בוצע בהצלחה" in result
        mock_wcapi.get.assert_called_once_with(f"orders/{order_id}")
        mock_wcapi.post.assert_called_once()

    def test_get_transaction_history(self, action_agent, mock_wcapi):
        # הגדרת נתוני בדיקה
        filters = {
            "after": "2024-01-01",
            "before": "2024-03-31",
            "status": "completed"
        }
        
        # הגדרת תגובת ה-API
        mock_wcapi.get.return_value.status_code = 200
        mock_wcapi.get.return_value.json.return_value = [
            {
                "id": 123,
                "date_paid": "2024-01-15T10:00:00",
                "total": "199.90",
                "payment_method_title": "העברה בנקאית",
                "status": "completed"
            },
            {
                "id": 124,
                "date_paid": "2024-02-01T15:30:00",
                "total": "299.90",
                "payment_method_title": "כרטיס אשראי",
                "status": "completed"
            }
        ]
        
        # הרצת הפונקציה
        result = action_agent.get_transaction_history(filters)
        
        # בדיקות
        assert "היסטוריית עסקאות" in result
        assert "199.90" in result
        assert "299.90" in result
        mock_wcapi.get.assert_called_once_with("orders", params={
            "per_page": 20,
            "orderby": "date",
            "order": "desc",
            **filters
        })

class TestCommandParsing:
    def test_extract_shipping_zone_command(self, action_agent):
        # בדיקת פקודת הוספת אזור משלוח
        message = "הוסף אזור משלוח שם: מרכז הארץ, אזורים: תל אביב;רמת גן;גבעתיים, מחיר: 25.90"
        result = action_agent._extract_shipping_zone_command(message)
        
        assert result["action"] == "add"
        assert result["name"] == "מרכז הארץ"
        assert result["regions"] == ["תל אביב", "רמת גן", "גבעתיים"]
        assert result["price"] == 25.90
        
        # בדיקת פקודת עדכון אזור משלוח
        message = "עדכן אזור משלוח 123 שם: מרכז מורחב, אזורים: תל אביב;רמת גן;גבעתיים;חולון, מחיר: 29.90"
        result = action_agent._extract_shipping_zone_command(message)
        
        assert result["action"] == "update"
        assert result["zone_id"] == 123
        assert result["name"] == "מרכז מורחב"
        assert result["regions"] == ["תל אביב", "רמת גן", "גבעתיים", "חולון"]
        assert result["price"] == 29.90

    def test_extract_shipping_label_command(self, action_agent):
        message = "הדפס תווית משלוח להזמנה 123 חברת שילוח: חברת שליחויות, שירות: משלוח מהיר"
        result = action_agent._extract_shipping_label_command(message)
        
        assert result["order_id"] == 123
        assert result["carrier"] == "חברת שליחויות"
        assert result["service"] == "משלוח מהיר"

    def test_extract_payment_command(self, action_agent):
        # בדיקת פקודת היסטוריית עסקאות
        message = "הצג היסטוריית עסקאות מתאריך: 2024-01-01, עד תאריך: 2024-03-31, סטטוס: completed"
        result = action_agent._extract_payment_command(message)
        
        assert result["action"] == "history"
        assert result["filters"]["after"] == "2024-01-01"
        assert result["filters"]["before"] == "2024-03-31"
        assert result["filters"]["status"] == "completed"
        
        # בדיקת פקודת עדכון שער חליפין
        message = "עדכן שער חליפין מטבע: USD, שער: 3.65"
        result = action_agent._extract_payment_command(message)
        
        assert result["action"] == "update_rate"
        assert result["currency"] == "USD"
        assert result["rate"] == 3.65 