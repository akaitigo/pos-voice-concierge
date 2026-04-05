package com.akaitigo.posvoice.query

import jakarta.annotation.security.RolesAllowed
import jakarta.inject.Inject
import jakarta.transaction.Transactional
import jakarta.ws.rs.Consumes
import jakarta.ws.rs.GET
import jakarta.ws.rs.POST
import jakarta.ws.rs.Path
import jakarta.ws.rs.Produces
import jakarta.ws.rs.QueryParam
import jakarta.ws.rs.core.MediaType
import jakarta.ws.rs.core.Response
import java.time.LocalDate
import java.time.LocalTime
import java.time.OffsetDateTime
import java.time.ZoneId

/**
 * 自然言語クエリ REST API.
 *
 * 売上集計、在庫照会、売上トップN、辞書管理のエンドポイントを提供する。
 * 全エンドポイントは Bearer Token (API Key) 認証で保護される。
 */
@Path("/api/query")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
@RolesAllowed("query-user")
class QueryResource {

    @Inject
    lateinit var salesRepository: SalesRepository

    companion object {
        private const val DEFAULT_TOP_N = 5
    }

    @Inject
    lateinit var inventoryRepository: InventoryRepository

    @Inject
    lateinit var aliasRepository: AliasRepository

    private val jstZone = ZoneId.of("Asia/Tokyo")

    /**
     * 売上集計 API.
     *
     * period: today, yesterday, this_week, last_week, this_month, last_month
     * product: 商品名（指定した場合は商品別売上）
     */
    @GET
    @Path("/sales")
    fun getSales(
        @QueryParam("period") period: String?,
        @QueryParam("product") product: String?,
    ): Response {
        val effectivePeriod = period ?: "today"
        val (from, to, label) = resolvePeriod(effectivePeriod)

        if (product != null) {
            val amount = salesRepository.productSalesBetween(product, from, to)
            return Response.ok(
                SalesResponse(
                    totalAmount = amount,
                    periodLabel = label,
                    itemCount = 0,
                    productName = product,
                ),
            ).build()
        }

        val totalAmount = salesRepository.totalSalesBetween(from, to)
        val itemCount = salesRepository.countSalesBetween(from, to)

        return Response.ok(
            SalesResponse(
                totalAmount = totalAmount,
                periodLabel = label,
                itemCount = itemCount.toInt(),
            ),
        ).build()
    }

    /**
     * 在庫照会 API.
     */
    @GET
    @Path("/inventory")
    fun getInventory(@QueryParam("product") product: String?): Response {
        if (product.isNullOrBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                .entity(mapOf("error" to "product パラメータは必須です"))
                .build()
        }

        val stock = inventoryRepository.findStockByProductName(product)
        return if (stock != null) {
            Response.ok(
                InventoryResponse(
                    productName = product,
                    stockQuantity = stock,
                ),
            ).build()
        } else {
            Response.status(Response.Status.NOT_FOUND)
                .entity(mapOf("error" to "商品が見つかりません: $product"))
                .build()
        }
    }

    /**
     * 売上トップN API.
     */
    @GET
    @Path("/top-products")
    fun getTopProducts(
        @QueryParam("period") period: String?,
        @QueryParam("limit") limit: Int?,
    ): Response {
        val effectivePeriod = period ?: "today"
        val effectiveLimit = limit ?: DEFAULT_TOP_N
        val (from, to, label) = resolvePeriod(effectivePeriod)

        val results = salesRepository.topProductsBetween(from, to, effectiveLimit)

        return Response.ok(
            TopProductsResponse(
                entries = results.map { r ->
                    TopProductEntryDto(
                        rank = r.rank,
                        productName = r.productName,
                        totalAmount = r.totalAmount,
                        quantitySold = r.quantitySold,
                    )
                },
                periodLabel = label,
            ),
        ).build()
    }

    /**
     * 表記ゆれ辞書に学習データを登録する.
     */
    @POST
    @Path("/learn-alias")
    @Transactional
    fun learnAlias(request: LearnAliasRequest): Response {
        if (request.recognizedText.isBlank() || request.correctProductName.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                .entity(mapOf("error" to "recognizedText と correctProductName は必須です"))
                .build()
        }

        aliasRepository.saveAlias(request.recognizedText, request.correctProductName)

        return Response.ok(
            mapOf(
                "success" to true,
                "message" to "「${request.recognizedText}」→「${request.correctProductName}」を辞書に登録しました",
            ),
        ).build()
    }

    /**
     * 辞書エクスポート API.
     */
    @GET
    @Path("/aliases/export")
    fun exportAliases(): Response {
        val aliases = aliasRepository.findAllAliases()
        val entries = aliases.map { a ->
            mapOf("alias" to a.alias, "product_name" to a.productName)
        }
        return Response.ok(entries).build()
    }

    /**
     * 辞書インポート API.
     */
    @POST
    @Path("/aliases/import")
    @Transactional
    fun importAliases(entries: List<AliasImportEntry>): Response {
        var count = 0
        for (entry in entries) {
            aliasRepository.saveAlias(entry.alias, entry.productName)
            count++
        }
        return Response.ok(
            mapOf(
                "success" to true,
                "importedCount" to count,
                "message" to "${count}件のエイリアスをインポートしました",
            ),
        ).build()
    }

    private fun resolvePeriod(period: String): Triple<OffsetDateTime, OffsetDateTime, String> {
        val today = LocalDate.now(jstZone)
        return when (period) {
            "today" -> {
                val from = today.atStartOfDay(jstZone).toOffsetDateTime()
                val to = today.plusDays(1).atStartOfDay(jstZone).toOffsetDateTime()
                Triple(from, to, "今日")
            }
            "yesterday" -> {
                val from = today.minusDays(1).atStartOfDay(jstZone).toOffsetDateTime()
                val to = today.atStartOfDay(jstZone).toOffsetDateTime()
                Triple(from, to, "昨日")
            }
            "this_week" -> {
                val monday = today.with(java.time.DayOfWeek.MONDAY)
                val from = monday.atStartOfDay(jstZone).toOffsetDateTime()
                val to = today.plusDays(1).atStartOfDay(jstZone).toOffsetDateTime()
                Triple(from, to, "今週")
            }
            "last_week" -> {
                val lastMonday = today.with(java.time.DayOfWeek.MONDAY).minusWeeks(1)
                val from = lastMonday.atStartOfDay(jstZone).toOffsetDateTime()
                val to = lastMonday.plusWeeks(1).atStartOfDay(jstZone).toOffsetDateTime()
                Triple(from, to, "先週")
            }
            "this_month" -> {
                val from = today.withDayOfMonth(1).atStartOfDay(jstZone).toOffsetDateTime()
                val to = today.plusDays(1).atStartOfDay(jstZone).toOffsetDateTime()
                Triple(from, to, "今月")
            }
            "last_month" -> {
                val firstOfLastMonth = today.minusMonths(1).withDayOfMonth(1)
                val from = firstOfLastMonth.atStartOfDay(jstZone).toOffsetDateTime()
                val to = today.withDayOfMonth(1).atStartOfDay(jstZone).toOffsetDateTime()
                Triple(from, to, "先月")
            }
            else -> {
                val from = today.atTime(LocalTime.MIN).atZone(jstZone).toOffsetDateTime()
                val to = today.plusDays(1).atStartOfDay(jstZone).toOffsetDateTime()
                Triple(from, to, "今日")
            }
        }
    }
}

data class SalesResponse(
    val totalAmount: Long,
    val periodLabel: String,
    val itemCount: Int,
    val productName: String? = null,
)

data class InventoryResponse(
    val productName: String,
    val stockQuantity: Int,
)

data class TopProductsResponse(
    val entries: List<TopProductEntryDto>,
    val periodLabel: String,
)

data class TopProductEntryDto(
    val rank: Int,
    val productName: String,
    val totalAmount: Long,
    val quantitySold: Int,
)

data class LearnAliasRequest(
    val recognizedText: String = "",
    val correctProductName: String = "",
)

data class AliasImportEntry(
    val alias: String = "",
    val productName: String = "",
)
