package com.akaitigo.posvoice.query

import io.quarkus.hibernate.orm.panache.kotlin.PanacheRepositoryBase
import jakarta.enterprise.context.ApplicationScoped
import jakarta.persistence.EntityManager
import jakarta.inject.Inject

@ApplicationScoped
class InventoryRepository : PanacheRepositoryBase<InventoryEntity, String> {

    @Inject
    lateinit var em: EntityManager

    /**
     * 商品名で在庫数を取得する.
     */
    fun findStockByProductName(productName: String): Int? {
        val result = em.createQuery(
            """
            SELECT i.quantity
            FROM InventoryEntity i JOIN ProductEntity p ON i.productId = p.id
            WHERE p.name = :name
            """.trimIndent(),
            Int::class.java,
        )
            .setParameter("name", productName)
            .resultList

        return result.firstOrNull()
    }
}
