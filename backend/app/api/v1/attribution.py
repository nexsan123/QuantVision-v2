"""
Phase 13: \u5f52\u56e0\u4e0e\u62a5\u8868 - API \u7aef\u70b9

\u63d0\u4f9b:
- Brinson \u5f52\u56e0 API
- \u56e0\u5b50\u5f52\u56e0 API
- TCA \u5206\u6790 API
- \u62a5\u8868\u5bfc\u51fa API
"""

import io
from datetime import date

import structlog
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.schemas.attribution import (
    AttributionReportType,
    BrinsonAttributionRequest,
    BrinsonResponse,
    ComprehensiveResponse,
    ExportReportRequest,
    FactorAttributionRequest,
    FactorResponse,
    ReportFormat,
    RiskFactorType,
    TCABenchmark,
    TCARequest,
    TCAResponse,
)
from app.services.attribution_service import (
    brinson_service,
    comprehensive_service,
    factor_service,
    tca_service,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/attribution", tags=["\u5f52\u56e0\u5206\u6790"])


# ============ Brinson \u5f52\u56e0 ============

@router.post("/brinson", response_model=BrinsonResponse)
async def calculate_brinson_attribution(
    request: BrinsonAttributionRequest,
) -> BrinsonResponse:
    """
    \u8ba1\u7b97 Brinson \u5f52\u56e0

    Brinson-Fachler \u6a21\u578b\u5206\u89e3\u8d85\u989d\u6536\u76ca\u4e3a:
    - \u914d\u7f6e\u6548\u5e94: \u884c\u4e1a\u914d\u7f6e\u51b3\u7b56\u7684\u8d21\u732e
    - \u9009\u80a1\u6548\u5e94: \u884c\u4e1a\u5185\u80a1\u7968\u9009\u62e9\u7684\u8d21\u732e
    - \u4ea4\u4e92\u6548\u5e94: \u914d\u7f6e\u4e0e\u9009\u80a1\u7684\u4ea4\u4e92\u4f5c\u7528
    """
    try:
        logger.info(
            "brinson_attribution_request",
            portfolio_id=request.portfolio_id,
            benchmark_id=request.benchmark_id,
        )

        result = await brinson_service.calculate_with_mock_data(request)

        return BrinsonResponse(success=True, data=result)

    except Exception as e:
        logger.error("brinson_attribution_error", error=str(e))
        return BrinsonResponse(success=False, error=str(e))


@router.get("/brinson/{portfolio_id}", response_model=BrinsonResponse)
async def get_brinson_attribution(
    portfolio_id: str,
    benchmark_id: str = Query("SPY", description="\u57fa\u51c6 ID"),
    start_date: date = Query(..., description="\u5f00\u59cb\u65e5\u671f"),
    end_date: date = Query(..., description="\u7ed3\u675f\u65e5\u671f"),
    frequency: str = Query("monthly", description="\u9891\u7387"),
) -> BrinsonResponse:
    """
    \u83b7\u53d6\u7ec4\u5408\u7684 Brinson \u5f52\u56e0
    """
    request = BrinsonAttributionRequest(
        portfolio_id=portfolio_id,
        benchmark_id=benchmark_id,
        start_date=start_date,
        end_date=end_date,
        frequency=frequency,
    )

    return await calculate_brinson_attribution(request)


# ============ \u56e0\u5b50\u5f52\u56e0 ============

@router.post("/factor", response_model=FactorResponse)
async def calculate_factor_attribution(
    request: FactorAttributionRequest,
) -> FactorResponse:
    """
    \u8ba1\u7b97\u56e0\u5b50\u5f52\u56e0

    \u57fa\u4e8e\u591a\u56e0\u5b50\u6a21\u578b\u5206\u89e3\u6536\u76ca:
    - \u5e02\u573a\u56e0\u5b50 (Market)
    - \u89c4\u6a21\u56e0\u5b50 (Size/SMB)
    - \u4ef7\u503c\u56e0\u5b50 (Value/HML)
    - \u52a8\u91cf\u56e0\u5b50 (Momentum)
    - \u8d28\u91cf\u56e0\u5b50 (Quality)
    - \u6ce2\u52a8\u56e0\u5b50 (Volatility)
    """
    try:
        logger.info(
            "factor_attribution_request",
            portfolio_id=request.portfolio_id,
            factors=request.factors,
        )

        result = await factor_service.calculate_with_mock_data(request)

        return FactorResponse(success=True, data=result)

    except Exception as e:
        logger.error("factor_attribution_error", error=str(e))
        return FactorResponse(success=False, error=str(e))


@router.get("/factor/{portfolio_id}", response_model=FactorResponse)
async def get_factor_attribution(
    portfolio_id: str,
    benchmark_id: str | None = Query(None, description="\u57fa\u51c6 ID"),
    start_date: date = Query(..., description="\u5f00\u59cb\u65e5\u671f"),
    end_date: date = Query(..., description="\u7ed3\u675f\u65e5\u671f"),
    factors: list[RiskFactorType] | None = Query(None, description="\u56e0\u5b50\u5217\u8868"),
) -> FactorResponse:
    """
    \u83b7\u53d6\u7ec4\u5408\u7684\u56e0\u5b50\u5f52\u56e0
    """
    request = FactorAttributionRequest(
        portfolio_id=portfolio_id,
        benchmark_id=benchmark_id,
        start_date=start_date,
        end_date=end_date,
        factors=factors,
    )

    return await calculate_factor_attribution(request)


@router.get("/factors", response_model=list[dict])
async def get_available_factors() -> list[dict]:
    """
    \u83b7\u53d6\u53ef\u7528\u7684\u98ce\u9669\u56e0\u5b50\u5217\u8868
    """
    factors = [
        {
            "id": RiskFactorType.MARKET.value,
            "name": "\u5e02\u573a",
            "description": "\u5e02\u573a\u98ce\u9669\u6ea2\u4ef7",
        },
        {
            "id": RiskFactorType.SIZE.value,
            "name": "\u89c4\u6a21",
            "description": "\u5c0f\u76d8\u80a1\u6ea2\u4ef7 (SMB)",
        },
        {
            "id": RiskFactorType.VALUE.value,
            "name": "\u4ef7\u503c",
            "description": "\u4ef7\u503c\u80a1\u6ea2\u4ef7 (HML)",
        },
        {
            "id": RiskFactorType.MOMENTUM.value,
            "name": "\u52a8\u91cf",
            "description": "\u8d62\u5bb6\u8f93\u5bb6\u6548\u5e94",
        },
        {
            "id": RiskFactorType.QUALITY.value,
            "name": "\u8d28\u91cf",
            "description": "\u9ad8\u8d28\u91cf\u80a1\u7968\u6ea2\u4ef7",
        },
        {
            "id": RiskFactorType.VOLATILITY.value,
            "name": "\u6ce2\u52a8",
            "description": "\u4f4e\u6ce2\u52a8\u5f02\u8c61",
        },
        {
            "id": RiskFactorType.DIVIDEND.value,
            "name": "\u80a1\u606f",
            "description": "\u9ad8\u80a1\u606f\u7387\u6ea2\u4ef7",
        },
        {
            "id": RiskFactorType.GROWTH.value,
            "name": "\u6210\u957f",
            "description": "\u9ad8\u6210\u957f\u80a1\u7968\u6ea2\u4ef7",
        },
    ]

    return factors


# ============ TCA \u5206\u6790 ============

@router.post("/tca", response_model=TCAResponse)
async def analyze_tca(
    request: TCARequest,
) -> TCAResponse:
    """
    \u4ea4\u6613\u6210\u672c\u5206\u6790 (TCA)

    \u5206\u6790\u5185\u5bb9:
    - \u6267\u884c\u7f3a\u53e3 (Implementation Shortfall)
    - \u4f63\u91d1\u3001\u6ed1\u70b9\u3001\u5e02\u573a\u51b2\u51fb
    - \u65f6\u673a\u6210\u672c\u3001\u673a\u4f1a\u6210\u672c
    """
    try:
        logger.info(
            "tca_analysis_request",
            portfolio_id=request.portfolio_id,
            strategy_id=request.strategy_id,
        )

        result = await tca_service.analyze_with_mock_data(request)

        return TCAResponse(success=True, data=result)

    except Exception as e:
        logger.error("tca_analysis_error", error=str(e))
        return TCAResponse(success=False, error=str(e))


@router.get("/tca/{portfolio_id}", response_model=TCAResponse)
async def get_tca(
    portfolio_id: str,
    start_date: date = Query(..., description="\u5f00\u59cb\u65e5\u671f"),
    end_date: date = Query(..., description="\u7ed3\u675f\u65e5\u671f"),
    symbols: list[str] | None = Query(None, description="\u80a1\u7968\u5217\u8868"),
    benchmark: TCABenchmark = Query(TCABenchmark.VWAP, description="\u57fa\u51c6\u7c7b\u578b"),
) -> TCAResponse:
    """
    \u83b7\u53d6\u7ec4\u5408\u7684 TCA \u5206\u6790
    """
    request = TCARequest(
        portfolio_id=portfolio_id,
        start_date=start_date,
        end_date=end_date,
        symbols=symbols,
        benchmark=benchmark,
    )

    return await analyze_tca(request)


@router.get("/tca/benchmarks", response_model=list[dict])
async def get_tca_benchmarks() -> list[dict]:
    """
    \u83b7\u53d6 TCA \u53ef\u7528\u57fa\u51c6
    """
    return [
        {
            "id": TCABenchmark.VWAP.value,
            "name": "VWAP",
            "description": "\u6210\u4ea4\u91cf\u52a0\u6743\u5e73\u5747\u4ef7",
        },
        {
            "id": TCABenchmark.TWAP.value,
            "name": "TWAP",
            "description": "\u65f6\u95f4\u52a0\u6743\u5e73\u5747\u4ef7",
        },
        {
            "id": TCABenchmark.ARRIVAL.value,
            "name": "Arrival Price",
            "description": "\u5230\u8fbe\u4ef7\u683c",
        },
    ]


# ============ \u7efc\u5408\u62a5\u544a ============

@router.get("/comprehensive/{portfolio_id}", response_model=ComprehensiveResponse)
async def get_comprehensive_attribution(
    portfolio_id: str,
    benchmark_id: str = Query("SPY", description="\u57fa\u51c6 ID"),
    start_date: date = Query(..., description="\u5f00\u59cb\u65e5\u671f"),
    end_date: date = Query(..., description="\u7ed3\u675f\u65e5\u671f"),
    include_brinson: bool = Query(True, description="\u5305\u542b Brinson \u5f52\u56e0"),
    include_factor: bool = Query(True, description="\u5305\u542b\u56e0\u5b50\u5f52\u56e0"),
    include_tca: bool = Query(True, description="\u5305\u542b TCA"),
) -> ComprehensiveResponse:
    """
    \u83b7\u53d6\u7efc\u5408\u5f52\u56e0\u62a5\u544a

    \u5305\u542b:
    - \u6536\u76ca\u6458\u8981
    - Brinson \u5f52\u56e0
    - \u56e0\u5b50\u5f52\u56e0
    - TCA \u5206\u6790
    - \u65f6\u5e8f\u6570\u636e
    """
    try:
        logger.info(
            "comprehensive_attribution_request",
            portfolio_id=portfolio_id,
            benchmark_id=benchmark_id,
        )

        result = await comprehensive_service.generate_report(
            portfolio_id=portfolio_id,
            portfolio_name=f"\u7ec4\u5408 {portfolio_id}",
            benchmark_id=benchmark_id,
            benchmark_name="S&P 500" if benchmark_id == "SPY" else benchmark_id,
            start_date=start_date,
            end_date=end_date,
            include_brinson=include_brinson,
            include_factor=include_factor,
            include_tca=include_tca,
        )

        return ComprehensiveResponse(success=True, data=result)

    except Exception as e:
        logger.error("comprehensive_attribution_error", error=str(e))
        return ComprehensiveResponse(success=False, error=str(e))


# ============ \u62a5\u8868\u5bfc\u51fa ============

@router.post("/export")
async def export_report(
    request: ExportReportRequest,
) -> StreamingResponse:
    """
    \u5bfc\u51fa\u5f52\u56e0\u62a5\u544a

    \u652f\u6301\u683c\u5f0f:
    - PDF: \u53ef\u6253\u5370\u62a5\u544a
    - Excel: \u6570\u636e\u8868\u683c
    - JSON: \u539f\u59cb\u6570\u636e
    """
    try:
        logger.info(
            "export_report_request",
            report_type=request.report_type,
            format=request.format,
        )

        # \u83b7\u53d6\u62a5\u544a\u6570\u636e
        report_data = await comprehensive_service.generate_report(
            portfolio_id=request.portfolio_id,
            portfolio_name=f"\u7ec4\u5408 {request.portfolio_id}",
            benchmark_id="SPY",
            benchmark_name="S&P 500",
            start_date=request.start_date,
            end_date=request.end_date,
            include_brinson=request.report_type in [AttributionReportType.BRINSON, AttributionReportType.COMPREHENSIVE],
            include_factor=request.report_type in [AttributionReportType.FACTOR, AttributionReportType.COMPREHENSIVE],
            include_tca=request.report_type in [AttributionReportType.TCA, AttributionReportType.COMPREHENSIVE],
        )

        if request.format == ReportFormat.JSON:
            # JSON \u683c\u5f0f
            import json
            content = json.dumps(report_data.model_dump(), indent=2, default=str)
            return StreamingResponse(
                io.BytesIO(content.encode("utf-8")),
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="attribution_report_{request.portfolio_id}.json"'
                },
            )

        elif request.format == ReportFormat.EXCEL:
            # Excel \u683c\u5f0f
            output = await _generate_excel_report(report_data, request)
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f'attachment; filename="attribution_report_{request.portfolio_id}.xlsx"'
                },
            )

        else:
            # PDF \u683c\u5f0f (\u7b80\u5316\u5b9e\u73b0)
            output = await _generate_pdf_report(report_data, request)
            return StreamingResponse(
                output,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="attribution_report_{request.portfolio_id}.pdf"'
                },
            )

    except Exception as e:
        logger.error("export_report_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report-types", response_model=list[dict])
async def get_report_types() -> list[dict]:
    """
    \u83b7\u53d6\u53ef\u7528\u7684\u62a5\u544a\u7c7b\u578b
    """
    return [
        {
            "id": AttributionReportType.BRINSON.value,
            "name": "Brinson \u5f52\u56e0",
            "description": "\u884c\u4e1a\u914d\u7f6e\u4e0e\u9009\u80a1\u6548\u5e94\u5206\u89e3",
        },
        {
            "id": AttributionReportType.FACTOR.value,
            "name": "\u56e0\u5b50\u5f52\u56e0",
            "description": "\u591a\u56e0\u5b50\u6a21\u578b\u6536\u76ca\u5206\u89e3",
        },
        {
            "id": AttributionReportType.TCA.value,
            "name": "TCA \u5206\u6790",
            "description": "\u4ea4\u6613\u6210\u672c\u5206\u6790",
        },
        {
            "id": AttributionReportType.COMPREHENSIVE.value,
            "name": "\u7efc\u5408\u62a5\u544a",
            "description": "\u5305\u542b\u6240\u6709\u5f52\u56e0\u5206\u6790",
        },
    ]


@router.get("/export-formats", response_model=list[dict])
async def get_export_formats() -> list[dict]:
    """
    \u83b7\u53d6\u53ef\u7528\u7684\u5bfc\u51fa\u683c\u5f0f
    """
    return [
        {
            "id": ReportFormat.PDF.value,
            "name": "PDF",
            "description": "\u53ef\u6253\u5370\u7684 PDF \u62a5\u544a",
        },
        {
            "id": ReportFormat.EXCEL.value,
            "name": "Excel",
            "description": "Excel \u6570\u636e\u8868\u683c",
        },
        {
            "id": ReportFormat.JSON.value,
            "name": "JSON",
            "description": "\u539f\u59cb JSON \u6570\u636e",
        },
    ]


# ============ \u8f85\u52a9\u51fd\u6570 ============

async def _generate_excel_report(
    report_data,
    request: ExportReportRequest,
) -> io.BytesIO:
    """
    \u751f\u6210 Excel \u62a5\u544a
    """
    try:
        import pandas as pd

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # \u6458\u8981\u9875
            summary_df = pd.DataFrame([{
                "\u7ec4\u5408\u6536\u76ca": f"{report_data.summary.portfolio_return:.2%}",
                "\u57fa\u51c6\u6536\u76ca": f"{report_data.summary.benchmark_return:.2%}",
                "\u8d85\u989d\u6536\u76ca": f"{report_data.summary.excess_return:.2%}",
                "\u4fe1\u606f\u6bd4\u7387": f"{report_data.summary.information_ratio:.2f}",
                "\u8ddf\u8e2a\u8bef\u5dee": f"{report_data.summary.tracking_error:.2%}",
                "\u590f\u666e\u6bd4\u7387": f"{report_data.summary.sharpe_ratio:.2f}",
                "\u6700\u5927\u56de\u64a4": f"{report_data.summary.max_drawdown:.2%}",
            }])
            summary_df.to_excel(writer, sheet_name="\u6458\u8981", index=False)

            # Brinson \u5f52\u56e0
            if report_data.brinson:
                brinson_data = []
                for sector in report_data.brinson.sector_details:
                    brinson_data.append({
                        "\u884c\u4e1a": sector.sector_name,
                        "\u7ec4\u5408\u6743\u91cd": f"{sector.portfolio_weight:.2%}",
                        "\u57fa\u51c6\u6743\u91cd": f"{sector.benchmark_weight:.2%}",
                        "\u914d\u7f6e\u6548\u5e94": f"{sector.allocation_effect:.4%}",
                        "\u9009\u80a1\u6548\u5e94": f"{sector.selection_effect:.4%}",
                        "\u4ea4\u4e92\u6548\u5e94": f"{sector.interaction_effect:.4%}",
                        "\u603b\u6548\u5e94": f"{sector.total_effect:.4%}",
                    })
                brinson_df = pd.DataFrame(brinson_data)
                brinson_df.to_excel(writer, sheet_name="Brinson\u5f52\u56e0", index=False)

            # \u56e0\u5b50\u5f52\u56e0
            if report_data.factor:
                factor_data = []
                for factor in report_data.factor.factor_contributions:
                    factor_data.append({
                        "\u56e0\u5b50": factor.factor_name,
                        "\u66b4\u9732": f"{factor.exposure:.2f}",
                        "\u56e0\u5b50\u6536\u76ca": f"{factor.factor_return:.2%}",
                        "\u8d21\u732e": f"{factor.contribution:.2%}",
                        "t\u7edf\u8ba1\u91cf": f"{factor.t_stat:.2f}",
                    })
                factor_df = pd.DataFrame(factor_data)
                factor_df.to_excel(writer, sheet_name="\u56e0\u5b50\u5f52\u56e0", index=False)

            # TCA
            if report_data.tca:
                tca_data = []
                for trade in report_data.tca.trades[:100]:  # \u9650\u5236 100 \u7b14
                    tca_data.append({
                        "\u4ea4\u6613ID": trade.trade_id,
                        "\u80a1\u7968": trade.symbol,
                        "\u65b9\u5411": trade.side,
                        "\u6570\u91cf": trade.quantity,
                        "\u51b3\u7b56\u4ef7": f"{trade.decision_price:.2f}",
                        "\u6267\u884c\u4ef7": f"{trade.execution_price:.2f}",
                        "\u6267\u884c\u7f3a\u53e3(\u57fa\u70b9)": f"{trade.implementation_shortfall_bps:.2f}",
                        "\u603b\u6210\u672c": f"{trade.costs.total_cost:.2f}",
                    })
                tca_df = pd.DataFrame(tca_data)
                tca_df.to_excel(writer, sheet_name="TCA\u5206\u6790", index=False)

        output.seek(0)
        return output

    except ImportError:
        # \u5982\u679c\u6ca1\u6709 pandas/openpyxl\uff0c\u8fd4\u56de\u7a7a\u6587\u4ef6
        return io.BytesIO(b"Excel export requires pandas and openpyxl")


async def _generate_pdf_report(
    report_data,
    request: ExportReportRequest,
) -> io.BytesIO:
    """
    \u751f\u6210 PDF \u62a5\u544a (\u7b80\u5316\u5b9e\u73b0)
    """
    # \u7b80\u5316\u5b9e\u73b0: \u751f\u6210\u6587\u672c\u62a5\u544a
    # \u5b9e\u9645\u751f\u4ea7\u73af\u5883\u5e94\u4f7f\u7528 reportlab \u6216 weasyprint
    lines = []
    lines.append("=" * 60)
    lines.append("\u5f52\u56e0\u5206\u6790\u62a5\u544a")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"\u7ec4\u5408: {report_data.portfolio_name}")
    lines.append(f"\u57fa\u51c6: {report_data.benchmark_name}")
    lines.append(f"\u65f6\u95f4\u6bb5: {report_data.period.start} \u81f3 {report_data.period.end}")
    lines.append(f"\u751f\u6210\u65f6\u95f4: {report_data.generated_at}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("\u6536\u76ca\u6458\u8981")
    lines.append("-" * 60)
    lines.append(f"\u7ec4\u5408\u6536\u76ca: {report_data.summary.portfolio_return:.2%}")
    lines.append(f"\u57fa\u51c6\u6536\u76ca: {report_data.summary.benchmark_return:.2%}")
    lines.append(f"\u8d85\u989d\u6536\u76ca: {report_data.summary.excess_return:.2%}")
    lines.append(f"\u4fe1\u606f\u6bd4\u7387: {report_data.summary.information_ratio:.2f}")
    lines.append(f"\u8ddf\u8e2a\u8bef\u5dee: {report_data.summary.tracking_error:.2%}")
    lines.append(f"\u590f\u666e\u6bd4\u7387: {report_data.summary.sharpe_ratio:.2f}")
    lines.append(f"\u6700\u5927\u56de\u64a4: {report_data.summary.max_drawdown:.2%}")
    lines.append("")

    if report_data.brinson:
        lines.append("-" * 60)
        lines.append("Brinson \u5f52\u56e0")
        lines.append("-" * 60)
        lines.append(f"\u914d\u7f6e\u6548\u5e94: {report_data.brinson.total_allocation_effect:.2%}")
        lines.append(f"\u9009\u80a1\u6548\u5e94: {report_data.brinson.total_selection_effect:.2%}")
        lines.append(f"\u4ea4\u4e92\u6548\u5e94: {report_data.brinson.total_interaction_effect:.2%}")
        lines.append(f"\u89e3\u8bfb: {report_data.brinson.interpretation}")
        lines.append("")

    if report_data.factor:
        lines.append("-" * 60)
        lines.append("\u56e0\u5b50\u5f52\u56e0")
        lines.append("-" * 60)
        lines.append(f"\u56e0\u5b50\u6536\u76ca: {report_data.factor.total_factor_return:.2%}")
        lines.append(f"\u7279\u8d28\u6536\u76ca: {report_data.factor.specific_return:.2%}")
        lines.append(f"\u89e3\u8bfb: {report_data.factor.interpretation}")
        lines.append("")

    if report_data.tca:
        lines.append("-" * 60)
        lines.append("TCA \u5206\u6790")
        lines.append("-" * 60)
        lines.append(f"\u603b\u4ea4\u6613\u6570: {report_data.tca.total_trades}")
        lines.append(f"\u603b\u4ea4\u6613\u989d: ${report_data.tca.total_notional:,.0f}")
        lines.append(f"\u5e73\u5747\u6210\u672c: {report_data.tca.avg_cost_bps:.2f} \u57fa\u70b9")
        lines.append("")

    lines.append("=" * 60)
    lines.append("\u62a5\u544a\u7ed3\u675f")
    lines.append("=" * 60)

    content = "\n".join(lines)
    return io.BytesIO(content.encode("utf-8"))
