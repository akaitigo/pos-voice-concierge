package com.akaitigo.posvoice.query

import io.quarkus.test.TestTransaction
import io.quarkus.test.junit.QuarkusTest
import jakarta.inject.Inject
import jakarta.persistence.EntityManager
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test
import java.time.OffsetDateTime
import java.time.ZoneOffset

/**
 * [SalesRepository] の実データテスト（H2）.
 *
 * Issue #26（商品別 itemCount）と Issue #29（型安全な topProductsBetween）を、
 * 実際に商品・売上行を投入して検証する。各テストは [TestTransaction] でロールバックし隔離する。
 */
@QuarkusTest
class SalesRepositoryTest {

    @Inject
    lateinit var salesRepository: SalesRepository

    @Inject
    lateinit var em: EntityManager

    private val from = OffsetDateTime.of(2026, 1, 1, 0, 0, 0, 0, ZoneOffset.UTC)
    private val to = OffsetDateTime.of(2026, 1, 2, 0, 0, 0, 0, ZoneOffset.UTC)
    private val soldAt = OffsetDateTime.of(2026, 1, 1, 10, 0, 0, 0, ZoneOffset.UTC)

    @Test
    @TestTransaction
    fun `countProductSalesBetween counts only matching product transactions`() {
        seedData()

        assertEquals(2L, salesRepository.countProductSalesBetween("コーラ", from, to))
        assertEquals(1L, salesRepository.countProductSalesBetween("お茶", from, to))
        assertEquals(0L, salesRepository.countProductSalesBetween("存在しない商品", from, to))
    }

    @Test
    @TestTransaction
    fun `productSalesBetween sums matching product totals`() {
        seedData()

        assertEquals(750L, salesRepository.productSalesBetween("コーラ", from, to))
        assertEquals(130L, salesRepository.productSalesBetween("お茶", from, to))
    }

    @Test
    @TestTransaction
    fun `topProductsBetween returns type-safe ranked aggregates`() {
        seedData()

        val top = salesRepository.topProductsBetween(from, to, 5)

        assertEquals(2, top.size)
        // コーラ: 450 + 300 = 750（数量 3 + 2 = 5）, お茶: 130（数量 1）
        assertEquals(1, top[0].rank)
        assertEquals("コーラ", top[0].productName)
        assertEquals(750L, top[0].totalAmount)
        assertEquals(5, top[0].quantitySold)
        assertEquals(2, top[1].rank)
        assertEquals("お茶", top[1].productName)
        assertEquals(130L, top[1].totalAmount)
        assertEquals(1, top[1].quantitySold)
    }

    @Test
    @TestTransaction
    fun `topProductsBetween honors the limit`() {
        seedData()

        val top = salesRepository.topProductsBetween(from, to, 1)

        assertEquals(1, top.size)
        assertEquals("コーラ", top[0].productName)
    }

    private fun seedData() {
        persistProduct("prod-cola", "コーラ", "4900000000001", 150)
        persistProduct("prod-tea", "お茶", "4900000000002", 130)
        persistSale("prod-cola", quantity = 3, unitPrice = 150, totalPrice = 450)
        persistSale("prod-cola", quantity = 2, unitPrice = 150, totalPrice = 300)
        persistSale("prod-tea", quantity = 1, unitPrice = 130, totalPrice = 130)
        em.flush()
    }

    private fun persistProduct(id: String, name: String, barcode: String, price: Int) {
        val product = ProductEntity()
        product.id = id
        product.name = name
        product.barcode = barcode
        product.price = price
        em.persist(product)
    }

    private fun persistSale(productId: String, quantity: Int, unitPrice: Int, totalPrice: Int) {
        val sale = SalesEntity()
        sale.productId = productId
        sale.quantity = quantity
        sale.unitPrice = unitPrice
        sale.totalPrice = totalPrice
        sale.soldAt = soldAt
        em.persist(sale)
    }
}
