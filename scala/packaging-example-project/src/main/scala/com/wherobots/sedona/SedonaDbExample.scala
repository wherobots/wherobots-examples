package com.wherobots.sedona

import org.apache.log4j.{Level, Logger}
import org.apache.sedona.core.formatMapper.shapefileParser.ShapefileReader
import org.apache.sedona.spark.SedonaContext
import org.apache.sedona.sql.utils.Adapter
import org.apache.spark.sql.SaveMode
import org.apache.spark.sql.functions.desc


object SedonaDbExample extends App {

  Logger.getRootLogger.setLevel(Level.WARN)
  Logger.getLogger("org.apache").setLevel(Level.WARN)
  Logger.getLogger("com").setLevel(Level.WARN)
  Logger.getLogger("akka").setLevel(Level.WARN)

  val s3BucketName = "wherobots-examples"
  val config = SedonaContext.builder()
    .config(s"spark.hadoop.fs.s3a.bucket.$s3BucketName.aws.credentials.provider","org.apache.hadoop.fs.s3a.AnonymousAWSCredentialsProvider")
    .getOrCreate()
	val sedona = SedonaContext.create(config)
  val sc = sedona.sparkContext

  // Read the countries shapefiles from S3
  val countries = ShapefileReader.readToGeometryRDD(sc, s"s3://$s3BucketName/data/ne_50m_admin_0_countries_lakes/")
  // Convert the Spatial RDD to a Spatial DataFrame using the Adapter
  val countries_df = Adapter.toDf(countries, sedona)
  countries_df.createOrReplaceTempView("country")
  countries_df.printSchema()

  // Read the airports shapefiles from S3
  val airports = ShapefileReader.readToGeometryRDD(sc, s"s3://$s3BucketName/data/ne_50m_airports/")
  // Convert the Spatial RDD to a Spatial DataFrame using the Adapter
  val airports_df = Adapter.toDf(airports, sedona)
  airports_df.createOrReplaceTempView("airport")
  airports_df.printSchema()

  // Run a spatial join query to find airports in each country
  val result = sedona.sql("SELECT c.geometry as country_geom, c.NAME_EN, a.geometry as airport_geom, a.name FROM country c, airport a WHERE ST_Contains(c.geometry, a.geometry)")
  // Aggregate the results to find the number of airports in each country
  val aggregateResult = result.groupBy("NAME_EN", "country_geom").count()
  aggregateResult.orderBy(desc("count")).show()

  // Write the results to a GeoParquet file
  aggregateResult.write.format("geoparquet").mode(SaveMode.Overwrite).save("airport_country.parquet")
}
