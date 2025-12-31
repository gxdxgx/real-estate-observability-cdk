import os
import json
from typing import Dict, Any, Optional
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from pydantic import BaseModel, ValidationError, Field
from shared.logging.logger import get_logger
from handlers.api.common.response import APIResponse

# Initialize AWS Lambda Powertools
logger = get_logger()
tracer = Tracer()
metrics = Metrics(namespace=os.getenv("POWERTOOLS_METRICS_NAMESPACE", "RealEstateObservability"))


# Request/Response models
class CashFlowRequest(BaseModel):
    """Cash flow calculation request model"""
    property_price: float = Field(..., gt=0, description="物件価格")
    loan_amount: float = Field(..., ge=0, description="融資金額")
    loan_term_years: int = Field(..., gt=0, le=50, description="返済年数")
    interest_rate: float = Field(..., gt=0, le=100, description="金利 (%)")
    monthly_rent: float = Field(..., ge=0, description="想定家賃（1ユニットあたり）")
    unit_count: int = Field(..., gt=0, description="ユニット数")
    vacancy_rate: float = Field(..., ge=0, le=100, description="空室率 (%)")
    management_fee_rate: float = Field(default=6, ge=0, le=20, description="管理費率 (%) - 収入の5～7%")
    insurance_monthly: float = Field(default=0, ge=0, description="保険料（月額）")
    maintenance_monthly: float = Field(default=0, ge=0, description="修繕費（月額）")
    common_area_utilities_monthly: float = Field(default=0, ge=0, description="共用部水道光熱費（月額）")
    tax_rate: float = Field(default=0, ge=0, le=50, description="税率 (%) - BTCFに対する税率")


class CashFlowResponse(BaseModel):
    """Cash flow calculation response model"""
    noi: float = Field(..., description="営業純利益（NOI）- 年間")
    btcf: float = Field(..., description="税引き前キャッシュフロー（BTCF）- 年間")
    atcf: float = Field(..., description="税引き後キャッシュフロー（ATCF）- 年間")
    monthly_noi: float = Field(..., description="営業純利益（NOI）- 月額")
    monthly_btcf: float = Field(..., description="税引き前キャッシュフロー（BTCF）- 月額")
    monthly_atcf: float = Field(..., description="税引き後キャッシュフロー（ATCF）- 月額")
    annual_loan_payment: float = Field(..., description="年間ローン返済額")
    monthly_loan_payment: float = Field(..., description="月額ローン返済額")
    annual_tax: float = Field(..., description="年間税金")
    breakdown: Dict[str, float]


@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics(raise_on_empty_metrics=False)
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    不動産投資のキャッシュフローを計算します。
    
    Expected body:
    {
        "property_price": 50000000,
        "loan_amount": 40000000,
        "loan_term_years": 30,
        "interest_rate": 2.5,
        "monthly_rent": 150000,
        "unit_count": 10,
        "vacancy_rate": 5,
        "management_fee_rate": 6,
        "insurance_monthly": 50000,
        "maintenance_monthly": 100000,
        "common_area_utilities_monthly": 30000,
        "tax_rate": 20
    }
    
    Returns:
        API Gateway response with cash flow calculation results
    """
    try:
        logger.info("Cash flow calculation requested", extra={"event": event})
        
        # Add custom metrics
        metrics.add_metric(name="CashFlowCalculations", unit=MetricUnit.Count, value=1)
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate request
        try:
            request = CashFlowRequest(**body)
        except ValidationError as e:
            logger.warning("Invalid request data", extra={"errors": e.errors()})
            return APIResponse.error(
                status_code=400,
                message="Invalid request data"
            )

        
        # 1. 営業純利益（NOI）の計算
        # 総家賃収入 = 家賃 * ユニット数
        total_monthly_rent = request.monthly_rent * request.unit_count
        
        # 空室損失を考慮した実効家賃収入
        effective_monthly_rent = total_monthly_rent * (1 - request.vacancy_rate / 100)
        
        # 管理費（収入の5～7%）
        monthly_management_fee = effective_monthly_rent * (request.management_fee_rate / 100)
        
        # NOI（月額）= 実効家賃収入 - 管理費 - 保険料 - 修繕費 - 共用部水道光熱費
        monthly_noi = (
            effective_monthly_rent -
            monthly_management_fee -
            request.insurance_monthly -
            request.maintenance_monthly -
            request.common_area_utilities_monthly
        )
        
        # NOI（年間）
        annual_noi = monthly_noi * 12
        
        # 2. 年間ローン返済額の計算
        monthly_interest_rate = (request.interest_rate / 100) / 12
        num_payments = request.loan_term_years * 12
        
        if request.loan_amount > 0 and monthly_interest_rate > 0:
            monthly_loan_payment = request.loan_amount * (
                monthly_interest_rate * (1 + monthly_interest_rate) ** num_payments
            ) / ((1 + monthly_interest_rate) ** num_payments - 1)
        else:
            monthly_loan_payment = 0
        
        annual_loan_payment = monthly_loan_payment * 12
        
        # 3. 税引き前キャッシュフロー（BTCF）の計算
        # BTCF（年間）= NOI - 年間ローン返済額
        annual_btcf = annual_noi - annual_loan_payment
        monthly_btcf = annual_btcf / 12
        
        # 4. 税引き後キャッシュフロー（ATCF）の計算
        # 税金 = BTCF * 税率
        annual_tax = annual_btcf * (request.tax_rate / 100)
        
        # ATCF（年間）= BTCF - 税金
        annual_atcf = annual_btcf - annual_tax
        monthly_atcf = annual_atcf / 12
        
        # Prepare breakdown
        breakdown = {
            "total_monthly_rent": total_monthly_rent,
            "vacancy_loss": total_monthly_rent - effective_monthly_rent,
            "effective_monthly_rent": effective_monthly_rent,
            "management_fee": monthly_management_fee,
            "insurance": request.insurance_monthly,
            "maintenance": request.maintenance_monthly,
            "common_area_utilities": request.common_area_utilities_monthly,
            "monthly_noi": monthly_noi,
            "annual_noi": annual_noi,
            "monthly_loan_payment": monthly_loan_payment,
            "annual_loan_payment": annual_loan_payment,
            "monthly_btcf": monthly_btcf,
            "annual_btcf": annual_btcf,
            "annual_tax": annual_tax,
            "monthly_atcf": monthly_atcf,
            "annual_atcf": annual_atcf
        }
        
        # Prepare response
        response_data = CashFlowResponse(
            noi=round(annual_noi, 2),
            btcf=round(annual_btcf, 2),
            atcf=round(annual_atcf, 2),
            monthly_noi=round(monthly_noi, 2),
            monthly_btcf=round(monthly_btcf, 2),
            monthly_atcf=round(monthly_atcf, 2),
            annual_loan_payment=round(annual_loan_payment, 2),
            monthly_loan_payment=round(monthly_loan_payment, 2),
            annual_tax=round(annual_tax, 2),
            breakdown={k: round(v, 2) for k, v in breakdown.items()}
        )
        
        logger.info("Cash flow calculation completed", extra={
            "noi": annual_noi,
            "btcf": annual_btcf,
            "atcf": annual_atcf
        })
        
        return APIResponse.success(
            data=response_data.model_dump()  # pydantic v2なら model_dump 推奨
        )
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return APIResponse.error(
            status_code=400,
            message="Invalid JSON in request body"
        )
    except Exception as e:
        logger.error("Error calculating cash flow", extra={"error": str(e)}, exc_info=True)
        metrics.add_metric(name="CashFlowCalculationErrors", unit=MetricUnit.Count, value=1)
        return APIResponse.error(
            status_code=500,
            message="Internal server error while calculating cash flow"
        )

