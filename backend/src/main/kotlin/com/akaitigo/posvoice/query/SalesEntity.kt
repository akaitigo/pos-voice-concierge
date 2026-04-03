package com.akaitigo.posvoice.query

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.GeneratedValue
import jakarta.persistence.GenerationType
import jakarta.persistence.Id
import jakarta.persistence.Table
import java.time.OffsetDateTime

@Entity
@Table(name = "sales")
class SalesEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long = 0

    @Column(name = "product_id", nullable = false)
    lateinit var productId: String

    @Column(nullable = false)
    var quantity: Int = 0

    @Column(name = "unit_price", nullable = false)
    var unitPrice: Int = 0

    @Column(name = "total_price", nullable = false)
    var totalPrice: Int = 0

    @Column(name = "sold_at", nullable = false)
    lateinit var soldAt: OffsetDateTime
}
