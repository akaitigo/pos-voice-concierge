package com.akaitigo.posvoice.query

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.Table
import java.time.OffsetDateTime

@Entity
@Table(name = "aliases")
class AliasEntity {

    @Id
    lateinit var alias: String

    @Column(name = "product_name", nullable = false)
    lateinit var productName: String

    @Column(name = "created_at", nullable = false)
    lateinit var createdAt: OffsetDateTime
}
