package com.akaitigo.posvoice.query

import io.quarkus.hibernate.orm.panache.kotlin.PanacheRepositoryBase
import jakarta.enterprise.context.ApplicationScoped
import jakarta.persistence.EntityManager
import jakarta.persistence.Tuple
import jakarta.inject.Inject
import java.time.OffsetDateTime

@ApplicationScoped
class SalesRepository : PanacheRepositoryBase<SalesEntity, Long> {

    @Inject
    lateinit var em: EntityManager

    /**
     * 指定期間の売上合計を取得する.
     */
    fun totalSalesBetween(from: OffsetDateTime, to: OffsetDateTime): Long {
        val result = em.createQuery(
            "SELECT COALESCE(SUM(s.totalPrice), 0) FROM SalesEntity s WHERE s.soldAt >= :from AND s.soldAt < :to",
            Long::class.java,
        )
            .setParameter("from", from)
            .setParameter("to", to)
            .singleResult
        return result ?: 0L
    }

    /**
     * 指定期間の売上件数を取得する.
     */
    fun countSalesBetween(from: OffsetDateTime, to: OffsetDateTime): Long {
        return count("soldAt >= ?1 and soldAt < ?2", from, to)
    }

    /**
     * 指定期間の商品別売上トップNを取得する.
     *
     * 型安全な [Tuple] クエリを使用し、非チェックキャストを排除する。
     * 集計値は DB 実装差（Long/BigInteger 等）を吸収するため [Number] として取り出す。
     */
    fun topProductsBetween(
        from: OffsetDateTime,
        to: OffsetDateTime,
        limit: Int,
    ): List<TopProductResult> {
        val results = em.createQuery(
            """
            SELECT p.name, SUM(s.totalPrice), SUM(s.quantity)
            FROM SalesEntity s JOIN ProductEntity p ON s.productId = p.id
            WHERE s.soldAt >= :from AND s.soldAt < :to
            GROUP BY p.name
            ORDER BY SUM(s.totalPrice) DESC
            """.trimIndent(),
            Tuple::class.java,
        )
            .setParameter("from", from)
            .setParameter("to", to)
            .setMaxResults(limit)
            .resultList

        return results.mapIndexed { index, tuple ->
            TopProductResult(
                rank = index + 1,
                productName = tuple.get(0, String::class.java),
                totalAmount = tuple.get(1, Number::class.java).toLong(),
                quantitySold = tuple.get(2, Number::class.java).toInt(),
            )
        }
    }

    /**
     * 指定商品の期間別売上合計を取得する.
     */
    fun productSalesBetween(
        productName: String,
        from: OffsetDateTime,
        to: OffsetDateTime,
    ): Long {
        val result = em.createQuery(
            """
            SELECT COALESCE(SUM(s.totalPrice), 0)
            FROM SalesEntity s JOIN ProductEntity p ON s.productId = p.id
            WHERE p.name = :name AND s.soldAt >= :from AND s.soldAt < :to
            """.trimIndent(),
            Long::class.java,
        )
            .setParameter("name", productName)
            .setParameter("from", from)
            .setParameter("to", to)
            .singleResult
        return result ?: 0L
    }

    /**
     * 指定商品の期間別売上件数（取引数）を取得する.
     */
    fun countProductSalesBetween(
        productName: String,
        from: OffsetDateTime,
        to: OffsetDateTime,
    ): Long {
        return em.createQuery(
            """
            SELECT COUNT(s)
            FROM SalesEntity s JOIN ProductEntity p ON s.productId = p.id
            WHERE p.name = :name AND s.soldAt >= :from AND s.soldAt < :to
            """.trimIndent(),
            Long::class.java,
        )
            .setParameter("name", productName)
            .setParameter("from", from)
            .setParameter("to", to)
            .singleResult
    }
}

data class TopProductResult(
    val rank: Int,
    val productName: String,
    val totalAmount: Long,
    val quantitySold: Int,
)
