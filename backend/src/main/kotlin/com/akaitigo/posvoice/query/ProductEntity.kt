package com.akaitigo.posvoice.query

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.Table

@Entity
@Table(name = "products")
class ProductEntity {

    @Id
    lateinit var id: String

    @Column(nullable = false, unique = true)
    lateinit var name: String

    @Column(nullable = false)
    lateinit var barcode: String

    @Column(nullable = false)
    var price: Int = 0
}
