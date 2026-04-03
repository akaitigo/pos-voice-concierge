package com.akaitigo.posvoice.query

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.Table
import java.time.OffsetDateTime

@Entity
@Table(name = "inventory")
class InventoryEntity {

    @Id
    @Column(name = "product_id")
    lateinit var productId: String

    @Column(nullable = false)
    var quantity: Int = 0

    @Column(name = "updated_at", nullable = false)
    lateinit var updatedAt: OffsetDateTime
}
