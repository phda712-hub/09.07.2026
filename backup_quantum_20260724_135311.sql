-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: quantum
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `bairros`
--

DROP TABLE IF EXISTS `bairros`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bairros` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `cidade` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `valor_entrega` double DEFAULT '0',
  `tempo_estimado` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bairros`
--

LOCK TABLES `bairros` WRITE;
/*!40000 ALTER TABLE `bairros` DISABLE KEYS */;
/*!40000 ALTER TABLE `bairros` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `caixa`
--

DROP TABLE IF EXISTS `caixa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `caixa` (
  `id` int NOT NULL AUTO_INCREMENT,
  `caixa_id` int DEFAULT '1',
  `status` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'fechado',
  `saldo_inicial` double DEFAULT '0',
  `transacoes` longtext COLLATE utf8mb4_unicode_ci,
  `data_abertura` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `usuario_abertura` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `nome` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT 'Caixa Principal',
  `usuario_fechamento` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_fechamento` datetime DEFAULT NULL,
  `total_creditos` decimal(15,4) DEFAULT '0.0000',
  `total_debitos` decimal(15,4) DEFAULT '0.0000',
  `saldo_final` decimal(15,4) DEFAULT '0.0000',
  `observacao` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `caixa`
--

LOCK TABLES `caixa` WRITE;
/*!40000 ALTER TABLE `caixa` DISABLE KEYS */;
INSERT INTO `caixa` VALUES (1,1,'fechado',0,'[]','','','2026-06-27 01:08:48','Caixa Principal','',NULL,0.0000,0.0000,0.0000,NULL);
/*!40000 ALTER TABLE `caixa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `caixa_movimentos`
--

DROP TABLE IF EXISTS `caixa_movimentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `caixa_movimentos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `caixa_id` int DEFAULT NULL,
  `caixa` varchar(120) DEFAULT '',
  `data` datetime DEFAULT CURRENT_TIMESTAMP,
  `tipo` varchar(50) DEFAULT '',
  `descricao` text,
  `valor` decimal(12,2) DEFAULT '0.00',
  `usuario` varchar(80) DEFAULT '',
  `forma_pagamento` varchar(80) DEFAULT '',
  `venda_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_caixa_data` (`data`),
  KEY `idx_caixa_movimentos_data` (`data`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `caixa_movimentos`
--

LOCK TABLES `caixa_movimentos` WRITE;
/*!40000 ALTER TABLE `caixa_movimentos` DISABLE KEYS */;
/*!40000 ALTER TABLE `caixa_movimentos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `caixas_pdv`
--

DROP TABLE IF EXISTS `caixas_pdv`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `caixas_pdv` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descricao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `local` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `banco` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `agencia` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `conta` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nome` (`nome`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `caixas_pdv`
--

LOCK TABLES `caixas_pdv` WRITE;
/*!40000 ALTER TABLE `caixas_pdv` DISABLE KEYS */;
INSERT INTO `caixas_pdv` VALUES (1,'Caixa Principal','Caixa principal do estabelecimento','Frente de Loja','','','',1,'2026-05-30 01:18:39','2026-05-30 01:18:39');
/*!40000 ALTER TABLE `caixas_pdv` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campanhas_farmacia`
--

DROP TABLE IF EXISTS `campanhas_farmacia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `campanhas_farmacia` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `tipo` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `descricao` text COLLATE utf8mb4_unicode_ci,
  `data_inicio` date DEFAULT NULL,
  `data_fim` date DEFAULT NULL,
  `canal` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `status` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT 'Ativa',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campanhas_farmacia`
--

LOCK TABLES `campanhas_farmacia` WRITE;
/*!40000 ALTER TABLE `campanhas_farmacia` DISABLE KEYS */;
/*!40000 ALTER TABLE `campanhas_farmacia` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campanhas_loja`
--

DROP TABLE IF EXISTS `campanhas_loja`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `campanhas_loja` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `tipo` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `descricao` text COLLATE utf8mb4_unicode_ci,
  `data_inicio` date DEFAULT NULL,
  `data_fim` date DEFAULT NULL,
  `canal` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `status` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT 'Ativa',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campanhas_loja`
--

LOCK TABLES `campanhas_loja` WRITE;
/*!40000 ALTER TABLE `campanhas_loja` DISABLE KEYS */;
/*!40000 ALTER TABLE `campanhas_loja` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cartoes`
--

DROP TABLE IF EXISTS `cartoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cartoes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `bandeira` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `tipo` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Crédito',
  `taxa_debito` double DEFAULT '0',
  `taxa_credito` double DEFAULT '0',
  `taxa_credito_parcelado` double DEFAULT '0',
  `dias_recebimento` int DEFAULT '30',
  `max_parcelas` int DEFAULT '1',
  `operadora` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `codigo_operadora` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ativo` int DEFAULT '1',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cartoes`
--

LOCK TABLES `cartoes` WRITE;
/*!40000 ALTER TABLE `cartoes` DISABLE KEYS */;
/*!40000 ALTER TABLE `cartoes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categorias`
--

DROP TABLE IF EXISTS `categorias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categorias` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `descricao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categorias`
--

LOCK TABLES `categorias` WRITE;
/*!40000 ALTER TABLE `categorias` DISABLE KEYS */;
INSERT INTO `categorias` VALUES (1,'Geral','Categoria padrão',1,'2026-05-30 01:18:39','2026-05-30 01:18:39'),(2,'Medicamentos','Medicamentos em geral',1,'2026-06-08 02:30:15','2026-06-08 02:30:15'),(3,'Perfumaria','Perfumaria, higiene e beleza',1,'2026-06-08 02:30:15','2026-06-08 02:30:15'),(4,'Controlados','Medicamentos controlados/receituário',1,'2026-06-08 02:30:15','2026-06-08 02:30:15'),(5,'Produtos','Produtos em geral',1,'2026-06-09 11:58:42','2026-06-09 11:58:42');
/*!40000 ALTER TABLE `categorias` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `centros_custo`
--

DROP TABLE IF EXISTS `centros_custo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `centros_custo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nome` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `descricao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `tipo` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'despesa',
  `orcamento_mensal` double DEFAULT '0',
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `centros_custo`
--

LOCK TABLES `centros_custo` WRITE;
/*!40000 ALTER TABLE `centros_custo` DISABLE KEYS */;
INSERT INTO `centros_custo` VALUES (1,'001','Vendas','Receitas de vendas','receita',0,1,'2026-05-30 01:18:39','2026-05-30 01:18:39'),(2,'002','Compras/Estoque','Custos com mercadorias','despesa',0,1,'2026-05-30 01:18:39','2026-05-30 01:18:39'),(3,'003','Despesas Operacionais','Despesas gerais de operação','despesa',0,1,'2026-05-30 01:18:39','2026-05-30 01:18:39'),(4,'004','Folha de Pagamento','Salários e encargos','despesa',0,1,'2026-05-30 01:18:39','2026-05-30 01:18:39'),(5,'005','Marketing','Publicidade e propaganda','despesa',0,1,'2026-05-30 01:18:39','2026-05-30 01:18:39'),(6,'006','Infraestrutura','Aluguel, água, luz, internet','despesa',0,1,'2026-05-30 01:18:39','2026-05-30 01:18:39'),(7,'007','Impostos','Tributos e taxas','despesa',0,1,'2026-05-30 01:18:39','2026-05-30 01:18:39'),(8,'008','Outros','Outras receitas/despesas','despesa',0,1,'2026-05-30 01:18:39','2026-05-30 01:18:39');
/*!40000 ALTER TABLE `centros_custo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clientes`
--

DROP TABLE IF EXISTS `clientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `clientes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `cpf` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `telefone` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `endereco` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `bairro` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `saldo_fidelidade` double DEFAULT '0',
  `saldo_credito` double DEFAULT '0',
  `email` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_nascimento` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `limite_credito` decimal(15,4) DEFAULT '0.0000',
  `convenio` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `plano_saude` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `lgpd_consentimento` tinyint DEFAULT '0',
  `data_ultima_compra` date DEFAULT NULL,
  `cpf_cnpj` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `whatsapp` varchar(60) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `cidade` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `uf` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `cep` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `atualizado_em` datetime DEFAULT NULL,
  `numero` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `idx_clientes_nome` (`nome`(191)),
  KEY `idx_clientes_cpf` (`cpf`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clientes`
--

LOCK TABLES `clientes` WRITE;
/*!40000 ALTER TABLE `clientes` DISABLE KEYS */;
INSERT INTO `clientes` VALUES (1,'Consumidor Final','','','','','',0,0,'','',1,'2026-05-30 01:18:39','2026-06-27 02:00:28',0.0000,'','',0,NULL,'','','','','',NULL,''),(2,'mario silva','','','','','',16.65,0,'','',1,'2026-06-27 01:40:44','2026-06-27 02:00:29',0.0000,'','',0,NULL,'','','','','',NULL,'');
/*!40000 ALTER TABLE `clientes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comandas`
--

DROP TABLE IF EXISTS `comandas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comandas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `numero` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `cliente` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Consumidor Final',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `itens` json DEFAULT NULL,
  `status` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'aberta',
  `sinalizada_para_fechar` int DEFAULT '0',
  `sinalizada_por` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `oculto_cozinha` int DEFAULT '0',
  `oculto_cozinha_por` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `oculto_cozinha_em` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `obs_cozinha_geral` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `obs_cozinha_geral_por` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `obs_cozinha_geral_em` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `reaberta_em` timestamp NULL DEFAULT NULL,
  `reaberta_por` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vezes_reaberta` int DEFAULT '0',
  `motivo_reabertura` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `mesa_id` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `mesa_numero` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `mesa_nome` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `cliente_id` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero` (`numero`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comandas`
--

LOCK TABLES `comandas` WRITE;
/*!40000 ALTER TABLE `comandas` DISABLE KEYS */;
/*!40000 ALTER TABLE `comandas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comandas_itens`
--

DROP TABLE IF EXISTS `comandas_itens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comandas_itens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `comanda_id` int NOT NULL DEFAULT '0',
  `produto_id` int DEFAULT NULL,
  `produto` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `quantidade` decimal(12,3) DEFAULT '0.000',
  `preco_unitario` decimal(12,2) DEFAULT '0.00',
  `subtotal` decimal(12,2) DEFAULT '0.00',
  `observacao` text COLLATE utf8mb4_unicode_ci,
  `criado_em` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comandas_itens`
--

LOCK TABLES `comandas_itens` WRITE;
/*!40000 ALTER TABLE `comandas_itens` DISABLE KEYS */;
/*!40000 ALTER TABLE `comandas_itens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `configuracoes`
--

DROP TABLE IF EXISTS `configuracoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `configuracoes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `chave` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `valor` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `categoria` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT 'sistema',
  `descricao` text COLLATE utf8mb4_unicode_ci,
  `atualizado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `chave` (`chave`),
  KEY `idx_configuracoes_chave` (`chave`)
) ENGINE=InnoDB AUTO_INCREMENT=144 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `configuracoes`
--

LOCK TABLES `configuracoes` WRITE;
/*!40000 ALTER TABLE `configuracoes` DISABLE KEYS */;
INSERT INTO `configuracoes` VALUES (1,'store_name','Sua Loja Aqui','2026-06-20 15:47:53','sistema',NULL,'2026-06-20 15:47:53','2026-06-16 01:01:45'),(2,'store_address','Seu Endereço Aqui, 123\nSua Cidade, UF - CEP 12345-678','2026-06-20 15:47:54','sistema',NULL,'2026-06-20 15:47:54','2026-06-16 01:01:45'),(3,'last_coupon_number','0','2026-06-20 15:47:56','sistema',NULL,'2026-06-20 15:47:56','2026-06-16 01:01:45'),(4,'last_comanda_number','0','2026-06-20 15:47:57','sistema',NULL,'2026-06-20 15:47:57','2026-06-16 01:01:45'),(5,'atacado_qtd_minima','10','2026-06-20 15:47:58','sistema',NULL,'2026-06-20 15:47:58','2026-06-16 01:01:45'),(6,'atacado_habilitado','True','2026-06-20 15:47:59','sistema',NULL,'2026-06-20 15:47:59','2026-06-16 01:01:45'),(7,'vendedor_obrigatorio','True','2026-06-20 15:48:00','sistema',NULL,'2026-06-20 15:48:00','2026-06-16 01:01:45'),(8,'imprimir_canhoto_loja','True','2026-06-20 15:48:06','sistema',NULL,'2026-06-20 15:48:06','2026-06-16 01:01:45'),(9,'acrescentar_taxa_cartao_pagamento','True','2026-06-20 15:48:07','sistema',NULL,'2026-06-20 15:48:07','2026-06-16 01:01:45'),(10,'taxa_garcom_ativa','False','2026-06-20 15:48:08','sistema',NULL,'2026-06-20 15:48:08','2026-06-16 01:01:45'),(11,'garcom_obrigatorio_pagamento','False','2026-06-20 15:48:09','sistema',NULL,'2026-06-20 15:48:09','2026-06-16 01:01:45'),(12,'modo_supermercado','False','2026-06-20 15:48:12','sistema',NULL,'2026-06-20 15:48:12','2026-06-16 01:01:45'),(13,'pagamento_mostrar_total_venda','True','2026-06-20 15:48:13','sistema',NULL,'2026-06-20 15:48:13','2026-06-16 01:01:45'),(14,'pagamento_mostrar_cliente','True','2026-06-20 15:48:15','sistema',NULL,'2026-06-20 15:48:15','2026-06-16 01:01:45'),(15,'pagamento_mostrar_entrega','True','2026-06-20 15:48:16','sistema',NULL,'2026-06-20 15:48:16','2026-06-16 01:01:45'),(16,'pagamento_mostrar_vendedor','True','2026-06-20 15:48:17','sistema',NULL,'2026-06-20 15:48:17','2026-06-16 01:01:45'),(17,'pagamento_mostrar_garcom_taxa','True','2026-06-20 15:48:18','sistema',NULL,'2026-06-20 15:48:18','2026-06-16 01:01:45'),(18,'licenca_hwid','DEE5D9F7BB1B5B6A0CB32FD190A2FBD8D0BEF13633A749F56FB29858461791C9','2026-06-20 15:48:19','sistema',NULL,'2026-06-20 15:48:19','2026-06-16 01:01:45'),(19,'licenca_dias','30','2026-06-20 15:48:20','sistema',NULL,'2026-06-20 15:48:20','2026-06-16 01:01:45'),(20,'licenca_contra_chave','C1E4-D042-5C08','2026-06-20 15:48:21','sistema',NULL,'2026-06-20 15:48:21','2026-06-16 01:01:45'),(21,'licenca_chave_ativacao','5D2E-FCCE-C156-662E','2026-06-20 15:48:22','sistema',NULL,'2026-06-20 15:48:22','2026-06-16 01:01:45'),(22,'licenca_data_ativacao','29/05/2026','2026-06-20 15:48:23','sistema',NULL,'2026-06-20 15:48:23','2026-06-16 01:01:45'),(23,'licenca_vencimento','28/06/2026','2026-06-20 15:48:24','sistema',NULL,'2026-06-20 15:48:24','2026-06-16 01:01:45'),(24,'data_vencimento_sistema','28/06/2026','2026-06-20 15:48:25','sistema',NULL,'2026-06-20 15:48:25','2026-06-16 01:01:45'),(25,'vencimento_sistema','28/06/2026','2026-06-20 15:48:26','sistema',NULL,'2026-06-20 15:48:26','2026-06-16 01:01:45'),(26,'licenca_status','Ativo','2026-06-20 15:48:27','sistema',NULL,'2026-06-20 15:48:27','2026-06-16 01:01:45'),(27,'status_licenca','Ativo','2026-06-20 15:48:28','sistema',NULL,'2026-06-20 15:48:28','2026-06-16 01:01:45'),(28,'licenca_atualizada_em','29/05/2026 22:19:58','2026-06-20 15:48:29','sistema',NULL,'2026-06-20 15:48:29','2026-06-16 01:01:45'),(29,'licenca_atualizada_por','adm','2026-06-20 15:48:30','sistema',NULL,'2026-06-20 15:48:30','2026-06-16 01:01:45'),(30,'licenca_algoritmo','HWID|DIAS|SALT|SECRET v4.0','2026-06-20 15:48:31','sistema',NULL,'2026-06-20 15:48:31','2026-06-16 01:01:45'),(31,'mesas_independentes_comandas','True','2026-06-20 15:48:31','sistema',NULL,'2026-06-20 15:48:31','2026-06-16 01:01:45'),(32,'alerta_validade_dias','15','2026-06-20 15:48:32','sistema',NULL,'2026-06-20 15:48:32','2026-06-16 01:01:45'),(34,'couvert_mesas_ativo','False','2026-06-20 15:48:10','sistema',NULL,'2026-06-20 15:48:10','2026-06-16 01:01:45'),(35,'taxa_couvert_mesas','0.0','2026-06-20 15:48:11','sistema',NULL,'2026-06-20 15:48:11','2026-06-16 01:01:45'),(54,'menu_relatorios_loja_visivel','0','2026-06-20 15:48:33','menus_loja','Exibe/oculta o menu Relatórios Loja','2026-06-20 15:48:33','2026-06-16 01:01:45'),(55,'menu_loja_pro_visivel','0','2026-06-20 15:48:34','menus_loja','Exibe/oculta o menu Loja Pro','2026-06-20 15:48:34','2026-06-16 01:01:45'),(56,'menu_atendimento_visivel','0','2026-06-20 15:48:35','menus_loja','Exibe/oculta o menu Atendimento','2026-06-20 15:48:35','2026-06-16 01:01:45'),(57,'menu_recompra_visivel','0','2026-06-20 15:48:36','menus_loja','Exibe/oculta o menu Recorrência','2026-06-20 15:48:36','2026-06-16 01:01:45'),(60,'farmacia_alerta_validade_dias','15','2026-06-20 15:48:37','farmacia','Dias antes para alertar lote/validade','2026-06-20 15:48:37','2026-06-16 01:01:45'),(61,'farmacia_preinit_schema_version','2026.06.05.1','2026-06-20 15:48:38','sistema','Versão da pré-inicialização estrutural','2026-06-20 15:48:38','2026-06-16 01:01:45'),(64,'menu_relatorios_farma_visivel','0','2026-06-20 15:48:39','menus_farmacia','Exibe/oculta o menu Relatórios Farma','2026-06-20 15:48:39','2026-06-16 01:01:45'),(65,'menu_farmacia_pro_visivel','0','2026-06-20 15:48:40','menus_farmacia','Exibe/oculta o menu Farmácia Pro','2026-06-20 15:48:40','2026-06-16 01:01:45'),(66,'menu_ambulatorio_visivel','0','2026-06-20 15:48:41','menus_farmacia','Exibe/oculta o menu Ambulatório','2026-06-20 15:48:41','2026-06-16 01:01:45'),(67,'menu_tratamento_visivel','0','2026-06-20 15:48:42','menus_farmacia','Exibe/oculta o menu Tratamentos','2026-06-20 15:48:42','2026-06-16 01:01:45'),(88,'perfil','AUTO','2026-06-20 15:47:40','sistema',NULL,'2026-06-20 15:47:40','2026-06-20 15:46:12'),(89,'porta','COM1','2026-06-20 15:47:41','sistema',NULL,'2026-06-20 15:47:41','2026-06-20 15:46:13'),(90,'baudrate','9600','2026-06-20 15:47:42','sistema',NULL,'2026-06-20 15:47:42','2026-06-20 15:46:14'),(91,'host','192.168.0.100','2026-06-20 15:47:43','sistema',NULL,'2026-06-20 15:47:43','2026-06-20 15:46:15'),(92,'tcp_port','9100','2026-06-20 15:47:44','sistema',NULL,'2026-06-20 15:47:44','2026-06-20 15:46:16'),(93,'intervalo_ms','350','2026-06-20 15:47:45','sistema',NULL,'2026-06-20 15:47:45','2026-06-20 15:46:17'),(94,'estabilidade_leituras','3','2026-06-20 15:47:46','sistema',NULL,'2026-06-20 15:47:46','2026-06-20 15:46:18'),(95,'auto_adicionar_checkout','False','2026-06-20 15:47:47','sistema',NULL,'2026-06-20 15:47:47','2026-06-20 15:46:19'),(96,'auto_self_service','False','2026-06-20 15:47:48','sistema',NULL,'2026-06-20 15:47:48','2026-06-20 15:46:20'),(97,'etiqueta_automatica','True','2026-06-20 15:47:49','sistema',NULL,'2026-06-20 15:47:49','2026-06-20 15:46:21'),(98,'prefixo_codigo_barras','20','2026-06-20 15:47:50','sistema',NULL,'2026-06-20 15:47:50','2026-06-20 15:46:22'),(99,'validade_dias','3','2026-06-20 15:47:51','sistema',NULL,'2026-06-20 15:47:51','2026-06-20 15:46:23'),(100,'layout_carga','GENERIC_CSV','2026-06-20 15:47:52','sistema',NULL,'2026-06-20 15:47:52','2026-06-20 15:46:24'),(101,'mostrar_vendedor_pagamento','False','2026-06-20 15:48:01','sistema',NULL,'2026-06-20 15:48:01','2026-06-20 15:46:33'),(102,'mostrar_total_venda_pagamento','False','2026-06-20 15:48:02','sistema',NULL,'2026-06-20 15:48:02','2026-06-20 15:46:34'),(103,'mostrar_botao_os_pagamento','False','2026-06-20 15:48:03','sistema',NULL,'2026-06-20 15:48:03','2026-06-20 15:46:35'),(104,'mostrar_cartoes_pagamento','False','2026-06-20 15:48:04','sistema',NULL,'2026-06-20 15:48:04','2026-06-20 15:46:36'),(105,'mostrar_alerta_vendedor_pagamento','False','2026-06-20 15:48:05','sistema',NULL,'2026-06-20 15:48:05','2026-06-20 15:46:37');
/*!40000 ALTER TABLE `configuracoes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contas_pagar`
--

DROP TABLE IF EXISTS `contas_pagar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contas_pagar` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `valor` double DEFAULT '0',
  `data_vencimento` text COLLATE utf8mb4_unicode_ci,
  `fornecedor_id` int DEFAULT NULL,
  `status` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Pendente',
  `data_pagamento` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `forma_pagamento` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fornecedor_id` (`fornecedor_id`),
  CONSTRAINT `contas_pagar_ibfk_1` FOREIGN KEY (`fornecedor_id`) REFERENCES `fornecedores` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contas_pagar`
--

LOCK TABLES `contas_pagar` WRITE;
/*!40000 ALTER TABLE `contas_pagar` DISABLE KEYS */;
/*!40000 ALTER TABLE `contas_pagar` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contas_receber`
--

DROP TABLE IF EXISTS `contas_receber`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contas_receber` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `valor` double DEFAULT '0',
  `data_vencimento` text COLLATE utf8mb4_unicode_ci,
  `cliente_id` int DEFAULT NULL,
  `status` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Pendente',
  `data_recebimento` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `forma_pagamento` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `venda_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `cliente_id` (`cliente_id`),
  CONSTRAINT `contas_receber_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contas_receber`
--

LOCK TABLES `contas_receber` WRITE;
/*!40000 ALTER TABLE `contas_receber` DISABLE KEYS */;
/*!40000 ALTER TABLE `contas_receber` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `creditos_clientes`
--

DROP TABLE IF EXISTS `creditos_clientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `creditos_clientes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int NOT NULL,
  `valor` double DEFAULT '0',
  `valor_original` double DEFAULT '0',
  `origem` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `venda_id` int DEFAULT NULL,
  `devolucao_id` int DEFAULT NULL,
  `data_criacao` text COLLATE utf8mb4_unicode_ci,
  `data_utilizacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `status` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Disponível',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `cliente_id` (`cliente_id`),
  CONSTRAINT `creditos_clientes_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `creditos_clientes`
--

LOCK TABLES `creditos_clientes` WRITE;
/*!40000 ALTER TABLE `creditos_clientes` DISABLE KEYS */;
/*!40000 ALTER TABLE `creditos_clientes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `crm_farmacia`
--

DROP TABLE IF EXISTS `crm_farmacia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crm_farmacia` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int DEFAULT NULL,
  `cliente_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `telefone_whatsapp` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `tipo_acao` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_retorno` date DEFAULT NULL,
  `status` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT 'Pendente',
  `mensagem` text COLLATE utf8mb4_unicode_ci,
  `observacao` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_crm_retorno` (`data_retorno`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `crm_farmacia`
--

LOCK TABLES `crm_farmacia` WRITE;
/*!40000 ALTER TABLE `crm_farmacia` DISABLE KEYS */;
/*!40000 ALTER TABLE `crm_farmacia` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `crm_loja`
--

DROP TABLE IF EXISTS `crm_loja`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crm_loja` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int DEFAULT NULL,
  `cliente_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `telefone_whatsapp` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `tipo_acao` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_retorno` date DEFAULT NULL,
  `status` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT 'Pendente',
  `mensagem` text COLLATE utf8mb4_unicode_ci,
  `observacao` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_crm_retorno` (`data_retorno`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `crm_loja`
--

LOCK TABLES `crm_loja` WRITE;
/*!40000 ALTER TABLE `crm_loja` DISABLE KEYS */;
/*!40000 ALTER TABLE `crm_loja` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customers`
--

DROP TABLE IF EXISTS `customers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cpf` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `telefone` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `whatsapp` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `endereco` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bairro` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `observacao` text COLLATE utf8mb4_unicode_ci,
  `criado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customers`
--

LOCK TABLES `customers` WRITE;
/*!40000 ALTER TABLE `customers` DISABLE KEYS */;
/*!40000 ALTER TABLE `customers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `devolucoes`
--

DROP TABLE IF EXISTS `devolucoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `devolucoes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `venda_id` int NOT NULL,
  `cupom_original` int DEFAULT NULL,
  `cliente_id` int DEFAULT NULL,
  `cliente_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `tipo_devolucao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'reembolso',
  `valor_total` double DEFAULT '0',
  `itens_devolvidos` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '[]',
  `motivo` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `usuario` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_devolucao` text COLLATE utf8mb4_unicode_ci,
  `credito_gerado_id` int DEFAULT NULL,
  `estornado` int DEFAULT '0',
  `data_estorno` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `usuario_estorno` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `motivo_estorno` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `venda_id` (`venda_id`),
  KEY `cliente_id` (`cliente_id`),
  CONSTRAINT `devolucoes_ibfk_1` FOREIGN KEY (`venda_id`) REFERENCES `vendas` (`id`),
  CONSTRAINT `devolucoes_ibfk_2` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `devolucoes`
--

LOCK TABLES `devolucoes` WRITE;
/*!40000 ALTER TABLE `devolucoes` DISABLE KEYS */;
/*!40000 ALTER TABLE `devolucoes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `empresa`
--

DROP TABLE IF EXISTS `empresa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `empresa` (
  `id` int NOT NULL,
  `nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Sua Empresa Aqui',
  `cnpj` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `endereco` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `telefone` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `email` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `cidade` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `estado` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `cep` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `chave_pix` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `logo_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `inscricao_estadual` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `inscricao_municipal` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `politica_troca` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `pix_banco` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `pix_titular` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `autorizacao_anvisa` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `responsavel_tecnico` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `crf_responsavel` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `razao_social` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `uf` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `atualizado_em` datetime DEFAULT NULL,
  `fantasia` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `whatsapp` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `bairro` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `empresa`
--

LOCK TABLES `empresa` WRITE;
/*!40000 ALTER TABLE `empresa` DISABLE KEYS */;
INSERT INTO `empresa` VALUES (1,'Sua Empresa Aqui','','Endereço não configurado','','','','','','','','','','','2026-05-30 01:18:39','','','','','','','',NULL,'','','');
/*!40000 ALTER TABLE `empresa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `entregadores`
--

DROP TABLE IF EXISTS `entregadores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `entregadores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `cpf` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `telefone` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `telefone2` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `veiculo` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Moto',
  `placa` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `cnh` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `endereco` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `bairro` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `pix` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `valor_entrega` double DEFAULT '5',
  `status` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Ativo',
  `data_admissao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `entregadores`
--

LOCK TABLES `entregadores` WRITE;
/*!40000 ALTER TABLE `entregadores` DISABLE KEYS */;
/*!40000 ALTER TABLE `entregadores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `estoque_lotes`
--

DROP TABLE IF EXISTS `estoque_lotes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `estoque_lotes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `produto_id` int NOT NULL,
  `produto_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `lote` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `validade` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_validade` date DEFAULT NULL,
  `quantidade` decimal(15,3) DEFAULT '0.000',
  `origem` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `nota_id` int DEFAULT NULL,
  `status` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT 'Ativo',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_lotes_produto` (`produto_id`),
  KEY `idx_lotes_validade` (`data_validade`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `estoque_lotes`
--

LOCK TABLES `estoque_lotes` WRITE;
/*!40000 ALTER TABLE `estoque_lotes` DISABLE KEYS */;
/*!40000 ALTER TABLE `estoque_lotes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fechamentos_caixa`
--

DROP TABLE IF EXISTS `fechamentos_caixa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fechamentos_caixa` (
  `id` int NOT NULL AUTO_INCREMENT,
  `caixa_id` int DEFAULT '1',
  `data_abertura` text COLLATE utf8mb4_unicode_ci,
  `data_fechamento` text COLLATE utf8mb4_unicode_ci,
  `saldo_inicial` double DEFAULT '0',
  `saldo_final` double DEFAULT '0',
  `total_entradas` double DEFAULT '0',
  `total_saidas` double DEFAULT '0',
  `usuario` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `transacoes` longtext COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fechamentos_caixa`
--

LOCK TABLES `fechamentos_caixa` WRITE;
/*!40000 ALTER TABLE `fechamentos_caixa` DISABLE KEYS */;
INSERT INTO `fechamentos_caixa` VALUES (1,1,'26/06/2026 22:08:48','27/06/2026 11:03:18',0,7437,0,0,'','[{\"hora\":\"22:08:48\",\"tipo\":\"CRÉDITO\",\"descricao\":\"SALDO INICIAL (ABERTURA) - Turno: Integral\",\"valor\":0.0,\"pagamento\":\"Dinheiro\",\"cliente\":\"adm\"},{\"hora\":\"22:09:01\",\"tipo\":\"CREDITO\",\"descricao\":\"Venda Cupom 1\",\"valor\":111.0,\"pagamento\":\"Dinheiro\",\"cliente\":\"Consumidor Final\"},{\"hora\":\"22:13:32\",\"tipo\":\"CREDITO\",\"descricao\":\"Venda Cupom 2\",\"valor\":5550.0,\"pagamento\":\"Dinheiro, Cartão Débito, Cartão Crédito, PIX\",\"cliente\":\"Consumidor Final\"},{\"hora\":\"22:41:12\",\"tipo\":\"CREDITO\",\"descricao\":\"Venda Cupom 3\",\"valor\":222.0,\"pagamento\":\"PIX\",\"cliente\":\"mario silva\"},{\"hora\":\"22:53:31\",\"tipo\":\"CREDITO\",\"descricao\":\"Venda Cupom 4\",\"valor\":111.0,\"pagamento\":\"Cartão Crédito\",\"cliente\":\"Consumidor Final\"},{\"hora\":\"23:00:02\",\"tipo\":\"CREDITO\",\"descricao\":\"Venda Cupom 5\",\"valor\":777.0,\"pagamento\":\"Cartão Débito\",\"cliente\":\"mario silva\"},{\"hora\":\"23:00:36\",\"tipo\":\"CREDITO\",\"descricao\":\"Venda Cupom 6\",\"valor\":666.0,\"pagamento\":\"Dinheiro, Cartão Débito\",\"cliente\":\"mario silva\"}]','2026-06-27 14:03:19');
/*!40000 ALTER TABLE `fechamentos_caixa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fornecedores`
--

DROP TABLE IF EXISTS `fornecedores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fornecedores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `cnpj` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `contato` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `telefone` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `email` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `endereco` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fornecedores`
--

LOCK TABLES `fornecedores` WRITE;
/*!40000 ALTER TABLE `fornecedores` DISABLE KEYS */;
/*!40000 ALTER TABLE `fornecedores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `itens_venda`
--

DROP TABLE IF EXISTS `itens_venda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `itens_venda` (
  `id` int NOT NULL AUTO_INCREMENT,
  `venda_id` int NOT NULL,
  `produto_id` int DEFAULT NULL,
  `codigo` varchar(80) DEFAULT '',
  `produto` varchar(255) DEFAULT '',
  `quantidade` decimal(12,3) DEFAULT '0.000',
  `unidade` varchar(30) DEFAULT '',
  `preco_unitario` decimal(12,2) DEFAULT '0.00',
  `subtotal` decimal(12,2) DEFAULT '0.00',
  `desconto` decimal(12,2) DEFAULT '0.00',
  PRIMARY KEY (`id`),
  KEY `idx_itens_venda_id` (`venda_id`),
  KEY `idx_itens_produto_id` (`produto_id`),
  KEY `idx_itens_venda_venda` (`venda_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `itens_venda`
--

LOCK TABLES `itens_venda` WRITE;
/*!40000 ALTER TABLE `itens_venda` DISABLE KEYS */;
/*!40000 ALTER TABLE `itens_venda` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lancamentos_centro_custo`
--

DROP TABLE IF EXISTS `lancamentos_centro_custo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lancamentos_centro_custo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `centro_custo_id` int DEFAULT NULL,
  `tipo` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'despesa',
  `descricao` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `valor` double DEFAULT '0',
  `data_lancamento` text COLLATE utf8mb4_unicode_ci,
  `data_competencia` text COLLATE utf8mb4_unicode_ci,
  `documento` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `usuario` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `centro_custo_id` (`centro_custo_id`),
  CONSTRAINT `lancamentos_centro_custo_ibfk_1` FOREIGN KEY (`centro_custo_id`) REFERENCES `centros_custo` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lancamentos_centro_custo`
--

LOCK TABLES `lancamentos_centro_custo` WRITE;
/*!40000 ALTER TABLE `lancamentos_centro_custo` DISABLE KEYS */;
/*!40000 ALTER TABLE `lancamentos_centro_custo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `movimentacoes_caixa`
--

DROP TABLE IF EXISTS `movimentacoes_caixa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `movimentacoes_caixa` (
  `id` int NOT NULL AUTO_INCREMENT,
  `caixa_id` int DEFAULT '1',
  `turno_id` int DEFAULT '1',
  `usuario` text COLLATE utf8mb4_unicode_ci,
  `tipo` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'abertura',
  `valor` double DEFAULT '0',
  `saldo_inicial` double DEFAULT '0',
  `saldo_final` double DEFAULT '0',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_hora` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `caixa_id` (`caixa_id`),
  KEY `turno_id` (`turno_id`),
  CONSTRAINT `movimentacoes_caixa_ibfk_1` FOREIGN KEY (`caixa_id`) REFERENCES `caixas_pdv` (`id`),
  CONSTRAINT `movimentacoes_caixa_ibfk_2` FOREIGN KEY (`turno_id`) REFERENCES `turnos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `movimentacoes_caixa`
--

LOCK TABLES `movimentacoes_caixa` WRITE;
/*!40000 ALTER TABLE `movimentacoes_caixa` DISABLE KEYS */;
/*!40000 ALTER TABLE `movimentacoes_caixa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notas_entrada`
--

DROP TABLE IF EXISTS `notas_entrada`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notas_entrada` (
  `id` int NOT NULL AUTO_INCREMENT,
  `numero_nota` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `fornecedor_id` int DEFAULT NULL,
  `fornecedor_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_entrada` text COLLATE utf8mb4_unicode_ci,
  `total` double DEFAULT '0',
  `itens` json DEFAULT NULL,
  `usuario` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `chave_nfe` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `serie` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `modelo` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `xml_path` text COLLATE utf8mb4_unicode_ci,
  `danfe_path` text COLLATE utf8mb4_unicode_ci,
  `status_conferencia` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT 'Pendente',
  `usuario_conferencia` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `preco` decimal(15,2) DEFAULT '0.00',
  `preco_venda` decimal(15,2) DEFAULT '0.00',
  `tamanho` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tamanho_id` int DEFAULT NULL,
  `lote` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `validade` date DEFAULT NULL,
  `controlar_lote_validade` tinyint DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `fornecedor_id` (`fornecedor_id`),
  KEY `idx_notas_numero` (`numero_nota`),
  CONSTRAINT `notas_entrada_ibfk_1` FOREIGN KEY (`fornecedor_id`) REFERENCES `fornecedores` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notas_entrada`
--

LOCK TABLES `notas_entrada` WRITE;
/*!40000 ALTER TABLE `notas_entrada` DISABLE KEYS */;
/*!40000 ALTER TABLE `notas_entrada` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orcamentos`
--

DROP TABLE IF EXISTS `orcamentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orcamentos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `numero` int DEFAULT NULL,
  `data` text COLLATE utf8mb4_unicode_ci,
  `validade` text COLLATE utf8mb4_unicode_ci,
  `cliente_id` int DEFAULT '1',
  `cliente_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Consumidor Final',
  `itens` json DEFAULT NULL,
  `subtotal` double DEFAULT '0',
  `desconto` double DEFAULT '0',
  `total` double DEFAULT '0',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `status` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Pendente',
  `usuario` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `venda_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `cliente_id` (`cliente_id`),
  CONSTRAINT `orcamentos_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orcamentos`
--

LOCK TABLES `orcamentos` WRITE;
/*!40000 ALTER TABLE `orcamentos` DISABLE KEYS */;
/*!40000 ALTER TABLE `orcamentos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orcamentos_itens`
--

DROP TABLE IF EXISTS `orcamentos_itens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orcamentos_itens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `orcamento_id` int NOT NULL DEFAULT '0',
  `produto_id` int DEFAULT NULL,
  `produto` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `quantidade` decimal(12,3) DEFAULT '0.000',
  `preco_unitario` decimal(12,2) DEFAULT '0.00',
  `subtotal` decimal(12,2) DEFAULT '0.00',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orcamentos_itens`
--

LOCK TABLES `orcamentos_itens` WRITE;
/*!40000 ALTER TABLE `orcamentos_itens` DISABLE KEYS */;
/*!40000 ALTER TABLE `orcamentos_itens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ordens_servico`
--

DROP TABLE IF EXISTS `ordens_servico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ordens_servico` (
  `id` int NOT NULL AUTO_INCREMENT,
  `numero` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `cliente_id` int DEFAULT '1',
  `cliente_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Consumidor Final',
  `cliente_telefone` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `cliente_email` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `cliente_endereco` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `tipo_equipamento` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `marca` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `modelo` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `numero_serie` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `cor` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `senha_equipamento` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `acessorios` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `defeito_relatado` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `defeito_constatado` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `status` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Aberta',
  `prioridade` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Normal',
  `tecnico_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_previsao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `servicos` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '[]',
  `pecas` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '[]',
  `valor_servicos` double DEFAULT '0',
  `valor_pecas` double DEFAULT '0',
  `desconto` double DEFAULT '0',
  `valor_total` double DEFAULT '0',
  `valor_pago` double DEFAULT '0',
  `valor_pendente` double DEFAULT '0',
  `forma_pagamento` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `garantia_dias` int DEFAULT '0',
  `data_garantia_fim` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `observacoes` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `observacoes_internas` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `historico` json DEFAULT NULL,
  `data_abertura` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_conclusao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_entrega` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_ultima_alteracao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `usuario_criacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `usuario_ultima_alteracao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero` (`numero`),
  KEY `cliente_id` (`cliente_id`),
  CONSTRAINT `ordens_servico_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ordens_servico`
--

LOCK TABLES `ordens_servico` WRITE;
/*!40000 ALTER TABLE `ordens_servico` DISABLE KEYS */;
/*!40000 ALTER TABLE `ordens_servico` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pbm_convenios`
--

DROP TABLE IF EXISTS `pbm_convenios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pbm_convenios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int DEFAULT NULL,
  `cliente_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `produto_id` int DEFAULT NULL,
  `medicamento` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `tipo` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `autorizacao` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `desconto_percentual` decimal(10,4) DEFAULT '0.0000',
  `validade_beneficio` date DEFAULT NULL,
  `observacao` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pbm_convenios`
--

LOCK TABLES `pbm_convenios` WRITE;
/*!40000 ALTER TABLE `pbm_convenios` DISABLE KEYS */;
/*!40000 ALTER TABLE `pbm_convenios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `produto_tamanhos`
--

DROP TABLE IF EXISTS `produto_tamanhos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `produto_tamanhos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `produto_id` int DEFAULT NULL,
  `tamanho_id` int DEFAULT NULL,
  `tamanho` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `codigo_barras` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `estoque` decimal(15,3) DEFAULT '0.000',
  `preco` decimal(15,2) DEFAULT '0.00',
  `preco_venda` decimal(15,2) DEFAULT '0.00',
  `ativo` tinyint DEFAULT '1',
  `criado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `produto_tamanhos`
--

LOCK TABLES `produto_tamanhos` WRITE;
/*!40000 ALTER TABLE `produto_tamanhos` DISABLE KEYS */;
/*!40000 ALTER TABLE `produto_tamanhos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `produtos`
--

DROP TABLE IF EXISTS `produtos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `produtos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `codigo_barras` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `categoria_id` int DEFAULT '1',
  `preco` double DEFAULT '0',
  `preco_atacado` double DEFAULT '0',
  `atacado_qtd_minima` double DEFAULT '10',
  `preco_promocional` double DEFAULT '0',
  `promocao_ativa` int DEFAULT '0',
  `promocao_inicio` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `promocao_fim` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `preco_compra` double DEFAULT '0',
  `tipo` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'unidade',
  `estoque` double DEFAULT '0',
  `estoque_minimo` double DEFAULT '5',
  `fidelidade_pontos` int DEFAULT '0',
  `tamanho_id` int DEFAULT NULL,
  `imagem` longtext COLLATE utf8mb4_unicode_ci,
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `ncm` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `cest` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `cfop` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `aliquota_icms` decimal(10,4) DEFAULT '0.0000',
  `aliquota_pis` decimal(10,4) DEFAULT '0.0000',
  `aliquota_cofins` decimal(10,4) DEFAULT '0.0000',
  `localizacao` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `curva_abc` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `margem_lucro` decimal(10,4) DEFAULT '0.0000',
  `ultima_compra` date DEFAULT NULL,
  `ultima_venda` date DEFAULT NULL,
  `preco_venda` decimal(15,2) DEFAULT '0.00',
  `preco_custo` decimal(15,2) DEFAULT '0.00',
  `valor` decimal(15,2) DEFAULT '0.00',
  `valor_venda` decimal(15,2) DEFAULT '0.00',
  `custo` decimal(15,2) DEFAULT '0.00',
  `tamanho` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `codigo` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `descricao` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `categoria` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `grupo` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `lote` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `validade` date DEFAULT NULL,
  `data_validade` date DEFAULT NULL,
  `controlar_lote_validade` tinyint DEFAULT '0',
  `unidade` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT 'unid.',
  `atualizado_em` datetime DEFAULT NULL,
  `fornecedor_id` int DEFAULT NULL,
  `medicamento` tinyint DEFAULT '0',
  `principio_ativo` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `laboratorio` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `registro_ms` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `controlado` tinyint DEFAULT '0',
  `uso_continuo` tinyint DEFAULT '0',
  `estoque_inicial` decimal(12,3) DEFAULT '0.000',
  PRIMARY KEY (`id`),
  KEY `categoria_id` (`categoria_id`),
  KEY `idx_produtos_barras` (`codigo_barras`),
  KEY `idx_produtos_nome` (`nome`(191)),
  KEY `idx_produtos_codigo` (`codigo`),
  KEY `idx_produtos_validade` (`data_validade`),
  KEY `idx_produtos_lote` (`lote`),
  CONSTRAINT `produtos_ibfk_1` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `produtos`
--

LOCK TABLES `produtos` WRITE;
/*!40000 ALTER TABLE `produtos` DISABLE KEYS */;
INSERT INTO `produtos` VALUES (1,'11111','7890001443844',1,111,111,1,0,0,'20/06/2026','20/06/2026',11,'unidade',111,1,0,NULL,'',1,'2026-06-20 14:32:28','2026-06-27 02:00:26','','','',0.0000,0.0000,0.0000,'','',0.0000,NULL,NULL,0.00,0.00,0.00,0.00,0.00,NULL,NULL,NULL,NULL,NULL,'','0000-00-00','0000-00-00',0,'unid.',NULL,NULL,0,'','','',0,0,0.000),(2,'6516516','7890001620962',2,111,111,1,0,0,'20/06/2026','20/06/2026',11,'unidade',44,1,0,NULL,'',1,'2026-06-27 01:07:53','2026-06-27 02:00:27','','','',0.0000,0.0000,0.0000,'','',0.0000,NULL,NULL,0.00,0.00,0.00,0.00,0.00,NULL,NULL,NULL,NULL,NULL,'','0000-00-00','0000-00-00',0,'unid.',NULL,NULL,0,'','','',0,0,0.000),(3,'cola quente5','7890001775617',2,225.3,220,1,0,0,'20/06/2026','20/06/2026',85.3,'unidade',95,10,0,NULL,'',1,'2026-06-27 10:45:37','2026-06-27 10:50:58','','','',0.0000,0.0000,0.0000,'','',0.0000,NULL,NULL,0.00,0.00,0.00,0.00,0.00,NULL,NULL,NULL,NULL,NULL,'','0000-00-00','0000-00-00',0,'unid.',NULL,NULL,0,'','','',0,0,0.000);
/*!40000 ALTER TABLE `produtos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `prontuario_ambulatorial`
--

DROP TABLE IF EXISTS `prontuario_ambulatorial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prontuario_ambulatorial` (
  `id` int NOT NULL AUTO_INCREMENT,
  `paciente_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `cliente_id` int DEFAULT NULL,
  `telefone` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `whatsapp` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `responsavel` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `profissional` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `registro_profissional` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `tipo_atendimento` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `classificacao_risco` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `pressao_arterial` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `frequencia_cardiaca` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `temperatura` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `spo2` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `glicemia` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `peso` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `altura` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `imc` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `queixa_principal` text COLLATE utf8mb4_unicode_ci,
  `anamnese` text COLLATE utf8mb4_unicode_ci,
  `alergias` text COLLATE utf8mb4_unicode_ci,
  `condicoes_conhecidas` text COLLATE utf8mb4_unicode_ci,
  `medicamentos_uso` text COLLATE utf8mb4_unicode_ci,
  `avaliacao_farmaceutica` text COLLATE utf8mb4_unicode_ci,
  `conduta` text COLLATE utf8mb4_unicode_ci,
  `orientacoes` text COLLATE utf8mb4_unicode_ci,
  `encaminhamento` text COLLATE utf8mb4_unicode_ci,
  `retorno_monitoramento` text COLLATE utf8mb4_unicode_ci,
  `observacoes_internas` text COLLATE utf8mb4_unicode_ci,
  `consentimento` tinyint DEFAULT '0',
  `data_atendimento` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_prontuario_data` (`data_atendimento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prontuario_ambulatorial`
--

LOCK TABLES `prontuario_ambulatorial` WRITE;
/*!40000 ALTER TABLE `prontuario_ambulatorial` DISABLE KEYS */;
/*!40000 ALTER TABLE `prontuario_ambulatorial` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `quantum_backup_automatico_ftp`
--

DROP TABLE IF EXISTS `quantum_backup_automatico_ftp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `quantum_backup_automatico_ftp` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ativo` tinyint DEFAULT '0',
  `host_ftp` varchar(255) DEFAULT '',
  `usuario_ftp` varchar(120) DEFAULT '',
  `senha_ftp` varchar(255) DEFAULT '',
  `pasta_remota` varchar(255) DEFAULT '',
  `intervalo_minutos` int DEFAULT '60',
  `ultimo_backup` datetime DEFAULT NULL,
  `ultimo_status` text,
  `criado_em` datetime DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `ultimo_arquivo` varchar(500) DEFAULT '',
  `ultimo_backup_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `quantum_backup_automatico_ftp`
--

LOCK TABLES `quantum_backup_automatico_ftp` WRITE;
/*!40000 ALTER TABLE `quantum_backup_automatico_ftp` DISABLE KEYS */;
INSERT INTO `quantum_backup_automatico_ftp` VALUES (1,0,'','','','',60,NULL,NULL,'2026-06-15 22:01:44','2026-06-15 22:01:44','',NULL);
/*!40000 ALTER TABLE `quantum_backup_automatico_ftp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `quantum_configuracoes_automaticas`
--

DROP TABLE IF EXISTS `quantum_configuracoes_automaticas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `quantum_configuracoes_automaticas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `chave` varchar(160) NOT NULL,
  `valor` longtext,
  `atualizado_em` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `grupo` varchar(80) DEFAULT 'geral',
  `descricao` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `chave` (`chave`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `quantum_configuracoes_automaticas`
--

LOCK TABLES `quantum_configuracoes_automaticas` WRITE;
/*!40000 ALTER TABLE `quantum_configuracoes_automaticas` DISABLE KEYS */;
/*!40000 ALTER TABLE `quantum_configuracoes_automaticas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `quantum_envio_mysql_externo`
--

DROP TABLE IF EXISTS `quantum_envio_mysql_externo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `quantum_envio_mysql_externo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ativo` tinyint(1) NOT NULL DEFAULT '0',
  `servidor_mysql` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nome_banco_mysql` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `usuario_mysql` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `senha_mysql` text COLLATE utf8mb4_unicode_ci,
  `criado_em` datetime DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `ultimo_sync_em` datetime DEFAULT NULL,
  `ultimo_status` text COLLATE utf8mb4_unicode_ci,
  `sync_pendente` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `quantum_envio_mysql_externo`
--

LOCK TABLES `quantum_envio_mysql_externo` WRITE;
/*!40000 ALTER TABLE `quantum_envio_mysql_externo` DISABLE KEYS */;
INSERT INTO `quantum_envio_mysql_externo` VALUES (1,0,'','','','','2026-06-20 11:29:56','2026-07-24 13:49:40',NULL,'Falha na sincronização MySQL externo: A API respondeu com conteúdo HTML em vez de JSON. Trecho: <!DOCTYPE html> <html lang=\"en\"> <head>     <meta charset=\"UTF-8\">     <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">     <title>Domain Suspended</title>     <script src=\"https://cdn.tailwindcss.com\"></script>     <script src=\"https://cdnjs.cloudflare.com/ajax/libs/js-cookie/3.0.1/js.cookie.min.js\"></script>     <style>         @import url(\'https://fonts.googleapis.com/css2',1);
/*!40000 ALTER TABLE `quantum_envio_mysql_externo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `receituario_controlados`
--

DROP TABLE IF EXISTS `receituario_controlados`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `receituario_controlados` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int DEFAULT NULL,
  `cliente_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `produto_id` int DEFAULT NULL,
  `medicamento` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `tipo_receita` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `numero_receita` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `prescritor` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `crm` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_receita` date DEFAULT NULL,
  `validade_receita` date DEFAULT NULL,
  `lote_dispensado` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `quantidade` decimal(15,3) DEFAULT '0.000',
  `sngpc` tinyint DEFAULT '0',
  `observacao` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_receita_validade` (`validade_receita`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `receituario_controlados`
--

LOCK TABLES `receituario_controlados` WRITE;
/*!40000 ALTER TABLE `receituario_controlados` DISABLE KEYS */;
/*!40000 ALTER TABLE `receituario_controlados` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recompras_continuos`
--

DROP TABLE IF EXISTS `recompras_continuos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recompras_continuos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int DEFAULT NULL,
  `cliente_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `produto_id` int DEFAULT NULL,
  `produto` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `dose_posologia` text COLLATE utf8mb4_unicode_ci,
  `consumo_por_dia` decimal(15,3) DEFAULT '1.000',
  `quantidade_comprada` decimal(15,3) DEFAULT '0.000',
  `intervalo_dias` int DEFAULT '30',
  `dias_antes_avisar` int DEFAULT '5',
  `data_inicio` date DEFAULT NULL,
  `data_compra` date DEFAULT NULL,
  `data_prevista_fim` date DEFAULT NULL,
  `data_lembrete` date DEFAULT NULL,
  `telefone_whatsapp` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ativo` tinyint DEFAULT '1',
  `continuo` tinyint DEFAULT '1',
  `observacao` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_trat_lembrete` (`data_lembrete`,`ativo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recompras_continuos`
--

LOCK TABLES `recompras_continuos` WRITE;
/*!40000 ALTER TABLE `recompras_continuos` DISABLE KEYS */;
/*!40000 ALTER TABLE `recompras_continuos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schema_migrations`
--

DROP TABLE IF EXISTS `schema_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `schema_migrations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `migration` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `aplicado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `nome` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=78 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schema_migrations`
--

LOCK TABLES `schema_migrations` WRITE;
/*!40000 ALTER TABLE `schema_migrations` DISABLE KEYS */;
INSERT INTO `schema_migrations` VALUES (1,'farmacia_preinit_schema_20260605','2026-06-08 02:30:15',''),(2,'loja_preinit_schema_20260605','2026-06-09 11:58:42',''),(3,'precheck_global_schema_20260614','2026-06-16 01:01:49',''),(4,'precheck_global_schema_20260614','2026-06-16 01:03:01',''),(5,'precheck_global_schema_20260614','2026-06-16 01:04:14',''),(6,'quantum_preboot_total_top','2026-06-20 14:29:56','quantum_preboot_total_top'),(7,'','2026-06-20 14:29:57','quantum_bootstrap_global_full'),(8,'precheck_global_schema_20260614','2026-06-20 14:29:59',''),(9,'quantum_preboot_total_top','2026-06-20 14:47:04','quantum_preboot_total_top'),(10,'','2026-06-20 14:47:04','quantum_bootstrap_global_full'),(11,'precheck_global_schema_20260614','2026-06-20 14:47:06',''),(12,'quantum_preboot_total_top','2026-06-20 15:42:58','quantum_preboot_total_top'),(13,'','2026-06-20 15:42:58','quantum_bootstrap_global_full'),(14,'precheck_global_schema_20260614','2026-06-20 15:43:00',''),(15,'quantum_preboot_total_top','2026-06-20 15:49:46','quantum_preboot_total_top'),(16,'','2026-06-20 15:49:47','quantum_bootstrap_global_full'),(17,'precheck_global_schema_20260614','2026-06-20 15:49:48',''),(18,'quantum_preboot_total_top','2026-06-20 16:16:54','quantum_preboot_total_top'),(19,'','2026-06-20 16:16:54','quantum_bootstrap_global_full'),(20,'precheck_global_schema_20260614','2026-06-20 16:16:56',''),(21,'quantum_preboot_total_top','2026-06-20 16:18:07','quantum_preboot_total_top'),(22,'','2026-06-20 16:18:07','quantum_bootstrap_global_full'),(23,'precheck_global_schema_20260614','2026-06-20 16:18:09',''),(24,'quantum_preboot_total_top','2026-06-20 16:21:08','quantum_preboot_total_top'),(25,'','2026-06-20 16:21:08','quantum_bootstrap_global_full'),(26,'precheck_global_schema_20260614','2026-06-20 16:21:10',''),(27,'quantum_preboot_total_top','2026-06-20 16:32:48','quantum_preboot_total_top'),(28,'','2026-06-20 16:32:48','quantum_bootstrap_global_full'),(29,'precheck_global_schema_20260614','2026-06-20 16:32:49',''),(30,'quantum_preboot_total_top','2026-06-20 16:36:52','quantum_preboot_total_top'),(31,'','2026-06-20 16:36:52','quantum_bootstrap_global_full'),(32,'precheck_global_schema_20260614','2026-06-20 16:36:54',''),(33,'quantum_preboot_total_top','2026-06-20 16:38:25','quantum_preboot_total_top'),(34,'','2026-06-20 16:38:26','quantum_bootstrap_global_full'),(35,'precheck_global_schema_20260614','2026-06-20 16:38:28',''),(36,'quantum_preboot_total_top','2026-06-20 16:38:31','quantum_preboot_total_top'),(37,'','2026-06-20 16:38:31','quantum_bootstrap_global_full'),(38,'quantum_preboot_total_top','2026-06-27 01:01:54','quantum_preboot_total_top'),(39,'','2026-06-27 01:01:55','quantum_bootstrap_global_full'),(40,'precheck_global_schema_20260614','2026-06-27 01:01:57',''),(41,'quantum_preboot_total_top','2026-06-27 01:39:52','quantum_preboot_total_top'),(42,'','2026-06-27 01:39:53','quantum_bootstrap_global_full'),(43,'precheck_global_schema_20260614','2026-06-27 01:39:55',''),(44,'quantum_preboot_total_top','2026-06-27 10:35:38','quantum_preboot_total_top'),(45,'','2026-06-27 10:35:39','quantum_bootstrap_global_full'),(46,'precheck_global_schema_20260614','2026-06-27 10:35:43',''),(47,'quantum_preboot_total_top','2026-06-27 10:38:36','quantum_preboot_total_top'),(48,'','2026-06-27 10:38:36','quantum_bootstrap_global_full'),(49,'precheck_global_schema_20260614','2026-06-27 10:38:39',''),(50,'quantum_preboot_total_top','2026-06-27 10:40:28','quantum_preboot_total_top'),(51,'','2026-06-27 10:40:28','quantum_bootstrap_global_full'),(52,'precheck_global_schema_20260614','2026-06-27 10:40:38',''),(53,'quantum_preboot_total_top','2026-06-27 11:00:26','quantum_preboot_total_top'),(54,'','2026-06-27 11:00:27','quantum_bootstrap_global_full'),(55,'precheck_global_schema_20260614','2026-06-27 11:00:29',''),(56,'quantum_preboot_total_top','2026-06-27 14:02:16','quantum_preboot_total_top'),(57,'','2026-06-27 14:02:16','quantum_bootstrap_global_full'),(58,'precheck_global_schema_20260614','2026-06-27 14:02:21',''),(59,'quantum_preboot_total_top','2026-07-07 20:36:49','quantum_preboot_total_top'),(60,'','2026-07-07 20:36:49','quantum_bootstrap_global_full'),(61,'quantum_preboot_total_top','2026-07-07 20:37:29','quantum_preboot_total_top'),(62,'','2026-07-07 20:37:29','quantum_bootstrap_global_full'),(63,'quantum_preboot_total_top','2026-07-07 20:40:26','quantum_preboot_total_top'),(64,'','2026-07-07 20:40:28','quantum_bootstrap_global_full'),(65,'precheck_global_schema_20260614','2026-07-07 20:40:29',''),(66,'quantum_preboot_total_top','2026-07-07 20:48:27','quantum_preboot_total_top'),(67,'','2026-07-07 20:48:27','quantum_bootstrap_global_full'),(68,'precheck_global_schema_20260614','2026-07-07 20:48:29',''),(69,'quantum_preboot_total_top','2026-07-08 20:49:17','quantum_preboot_total_top'),(70,'','2026-07-08 20:49:18','quantum_bootstrap_global_full'),(71,'precheck_global_schema_20260614','2026-07-08 20:49:21',''),(72,'quantum_preboot_total_top','2026-07-09 21:05:33','quantum_preboot_total_top'),(73,'','2026-07-09 21:05:33','quantum_bootstrap_global_full'),(74,'precheck_global_schema_20260614','2026-07-09 21:05:38',''),(75,'quantum_preboot_total_top','2026-07-24 16:48:40','quantum_preboot_total_top'),(76,'','2026-07-24 16:48:41','quantum_bootstrap_global_full'),(77,'precheck_global_schema_20260614','2026-07-24 16:48:43','');
/*!40000 ALTER TABLE `schema_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sequencias`
--

DROP TABLE IF EXISTS `sequencias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sequencias` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `valor` int DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `nome` (`nome`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sequencias`
--

LOCK TABLES `sequencias` WRITE;
/*!40000 ALTER TABLE `sequencias` DISABLE KEYS */;
INSERT INTO `sequencias` VALUES (1,'nota_entrada',0),(2,'ordem_servico',0);
/*!40000 ALTER TABLE `sequencias` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `servicos`
--

DROP TABLE IF EXISTS `servicos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `servicos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `descricao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `categoria` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Outros',
  `preco` double DEFAULT '0',
  `duracao_estimada` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'A combinar',
  `unidade_cobranca` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Por serviço',
  `status` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Ativo',
  `codigo` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `garantia` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Sem garantia',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `servicos`
--

LOCK TABLES `servicos` WRITE;
/*!40000 ALTER TABLE `servicos` DISABLE KEYS */;
/*!40000 ALTER TABLE `servicos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `servicos_farmaceuticos`
--

DROP TABLE IF EXISTS `servicos_farmaceuticos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `servicos_farmaceuticos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int DEFAULT NULL,
  `cliente_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `servico` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_agendada` datetime DEFAULT NULL,
  `profissional` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `status` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT 'Agendado',
  `valor` decimal(15,4) DEFAULT '0.0000',
  `observacao` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_servicos_agenda` (`data_agendada`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `servicos_farmaceuticos`
--

LOCK TABLES `servicos_farmaceuticos` WRITE;
/*!40000 ALTER TABLE `servicos_farmaceuticos` DISABLE KEYS */;
/*!40000 ALTER TABLE `servicos_farmaceuticos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tamanhos`
--

DROP TABLE IF EXISTS `tamanhos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tamanhos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `sigla` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ordem` int DEFAULT '0',
  `tipo` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Roupa',
  `descricao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tamanhos`
--

LOCK TABLES `tamanhos` WRITE;
/*!40000 ALTER TABLE `tamanhos` DISABLE KEYS */;
/*!40000 ALTER TABLE `tamanhos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tamanhos_produtos`
--

DROP TABLE IF EXISTS `tamanhos_produtos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tamanhos_produtos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `produto_id` int DEFAULT NULL,
  `nome` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tamanho` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `descricao` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `estoque` decimal(15,3) DEFAULT '0.000',
  `preco` decimal(15,2) DEFAULT '0.00',
  `preco_venda` decimal(15,2) DEFAULT '0.00',
  `ativo` tinyint DEFAULT '1',
  `criado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `tamanho_id` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tamanhos_produtos`
--

LOCK TABLES `tamanhos_produtos` WRITE;
/*!40000 ALTER TABLE `tamanhos_produtos` DISABLE KEYS */;
/*!40000 ALTER TABLE `tamanhos_produtos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tratamentos_continuos`
--

DROP TABLE IF EXISTS `tratamentos_continuos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tratamentos_continuos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int DEFAULT NULL,
  `cliente_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `produto_id` int DEFAULT NULL,
  `medicamento` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `dose_posologia` text COLLATE utf8mb4_unicode_ci,
  `consumo_por_dia` decimal(15,3) DEFAULT '1.000',
  `quantidade_comprada` decimal(15,3) DEFAULT '0.000',
  `intervalo_dias` int DEFAULT '30',
  `dias_antes_avisar` int DEFAULT '5',
  `data_inicio` date DEFAULT NULL,
  `data_compra` date DEFAULT NULL,
  `data_prevista_fim` date DEFAULT NULL,
  `data_lembrete` date DEFAULT NULL,
  `telefone_whatsapp` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ativo` tinyint DEFAULT '1',
  `continuo` tinyint DEFAULT '1',
  `observacao` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_trat_lembrete` (`data_lembrete`,`ativo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tratamentos_continuos`
--

LOCK TABLES `tratamentos_continuos` WRITE;
/*!40000 ALTER TABLE `tratamentos_continuos` DISABLE KEYS */;
/*!40000 ALTER TABLE `tratamentos_continuos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `turnos`
--

DROP TABLE IF EXISTS `turnos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `turnos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `hora_inicio` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '00:00',
  `hora_fim` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '23:59',
  `descricao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `turnos`
--

LOCK TABLES `turnos` WRITE;
/*!40000 ALTER TABLE `turnos` DISABLE KEYS */;
INSERT INTO `turnos` VALUES (1,'Manhã','06:00','12:00','Turno da manhã',1,'2026-05-30 01:18:39'),(2,'Tarde','12:00','18:00','Turno da tarde',1,'2026-05-30 01:18:39'),(3,'Noite','18:00','00:00','Turno da noite',1,'2026-05-30 01:18:39'),(4,'Integral','00:00','23:59','Turno integral',1,'2026-05-30 01:18:39');
/*!40000 ALTER TABLE `turnos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_log`
--

DROP TABLE IF EXISTS `user_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario` text COLLATE utf8mb4_unicode_ci,
  `acao` text COLLATE utf8mb4_unicode_ci,
  `detalhes` text COLLATE utf8mb4_unicode_ci,
  `datahora` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_log`
--

LOCK TABLES `user_log` WRITE;
/*!40000 ALTER TABLE `user_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `nivel_acesso` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'caixa',
  `permissoes` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '[]',
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `usuario` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nome` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `senha` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nivel` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vinculos` longtext COLLATE utf8mb4_unicode_ci,
  `bloqueado` tinyint DEFAULT '0',
  `criado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` timestamp NULL DEFAULT NULL,
  `protegido` tinyint DEFAULT '0',
  `perfil` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT 'Operador',
  `admin_original` tinyint DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `idx_usuarios_username` (`username`),
  KEY `idx_usuarios_usuario` (`usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'adm','716a3ef91adceabfc44435ff688d87fbdb9b6ae45f392de47244177dafe9eb06','admin','[\"*\"]',1,'2026-05-30 01:18:39','2026-05-30 01:22:22',NULL,NULL,NULL,NULL,NULL,NULL,0,'2026-06-08 02:30:23',NULL,0,'Operador',0),(2,'phda','$2b$12$Xo96dzT3IIr6gjvGNGqXReeOAecNR.jV3Y1jH.XJbiYqyrX4o2CGy','admin','[\"*\"]',1,'2026-05-30 01:18:42','2026-05-30 01:22:22',NULL,NULL,NULL,NULL,NULL,NULL,0,'2026-06-08 02:30:23',NULL,0,'Operador',0);
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vendas`
--

DROP TABLE IF EXISTS `vendas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vendas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `coupon_number` int DEFAULT NULL,
  `timestamp` text COLLATE utf8mb4_unicode_ci,
  `data` text COLLATE utf8mb4_unicode_ci,
  `cliente_id` int DEFAULT '1',
  `cliente_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Consumidor Final',
  `total` double DEFAULT '0',
  `formas_pagamento` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '{}',
  `troco` double DEFAULT '0',
  `usuario` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `is_delivery` int DEFAULT '0',
  `itens` json DEFAULT NULL,
  `entregador_id` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `entregador_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `entrega_concluida` int DEFAULT '0',
  `data_entrega_concluida` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `vendedor_id` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `vendedor_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `desconto` double DEFAULT '0',
  `acrescimo` double DEFAULT '0',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `canal_venda` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT 'Balcão',
  `prescricao_obrigatoria` tinyint DEFAULT '0',
  `pbm_autorizacao` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `delivery` tinyint DEFAULT '0',
  `caixa` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `subtotal` decimal(12,2) DEFAULT '0.00',
  `forma_pagamento` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'finalizada',
  `numero` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_venda` datetime DEFAULT NULL,
  `operador` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `taxa_entrega` decimal(15,4) DEFAULT '0.0000',
  `tipo` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `caixa_id` int DEFAULT NULL,
  `caixa_nome` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `cliente_id` (`cliente_id`),
  KEY `idx_vendas_data` (`data_venda`),
  KEY `idx_vendas_usuario` (`usuario`),
  CONSTRAINT `vendas_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vendas`
--

LOCK TABLES `vendas` WRITE;
/*!40000 ALTER TABLE `vendas` DISABLE KEYS */;
INSERT INTO `vendas` VALUES (1,1,'2026-06-26T22:08:57.308734','26/06/2026',1,'Consumidor Final',111,'{\"Dinheiro\": 111.0}',0,'adm',0,'{\"2\": {\"id\": \"2\", \"nome\": \"6516516\", \"tipo\": \"unidade\", \"preco\": 111.0, \"desconto\": 0.0, \"acrescimo\": 0.0, \"nome_original\": \"6516516\", \"preco_original\": 111.0, \"quantidade_peso\": 1, \"preco_atacado_aplicado\": true, \"preco_promocional_aplicado\": false}}',NULL,'',0,'','','',0,0,'','2026-06-27 01:08:59','Balcão',0,'',0,'',0.00,'','finalizada','',NULL,'',0.0000,'',NULL,''),(2,2,'2026-06-26T22:13:28.041324','26/06/2026',1,'Consumidor Final',5550,'{\"Dinheiro\": 199.0, \"CartaoDebito\": 1970.5, \"CartaoDebito_Bandeira\": \"\", \"CartaoDebito_ID\": \"\", \"CartaoDebito_Taxa\": 0.0, \"CartaoDebito_Taxa_Acrescimo_Ativo\": false, \"CartaoDebito_Valor_Original\": 2169.5, \"CartaoDebito_Valor_Taxa\": 0.0, \"CartaoDebito_Parcelas\": 1, \"CartaoCredito\": 2790.0, \"CartaoCredito_Bandeira\": \"\", \"CartaoCredito_ID\": \"\", \"CartaoCredito_Taxa\": 0.0, \"CartaoCredito_Taxa_Acrescimo_Ativo\": false, \"CartaoCredito_Valor_Original\": 4959.5, \"CartaoCredito_Valor_Taxa\": 0.0, \"CartaoCred',0,'adm',0,'{\"2\": {\"id\": \"2\", \"nome\": \"6516516\", \"tipo\": \"unidade\", \"preco\": 111.0, \"desconto\": 0.0, \"acrescimo\": 0.0, \"nome_original\": \"6516516\", \"preco_original\": 111.0, \"quantidade_peso\": 50, \"preco_atacado_aplicado\": true, \"preco_promocional_aplicado\": false}}',NULL,'',0,'','','',0,0,'','2026-06-27 01:13:31','Balcão',0,'',0,'',0.00,'','finalizada','',NULL,'',0.0000,'',NULL,''),(3,3,'2026-06-26T22:41:06.231587','26/06/2026',2,'mario silva',222,'{\"PIX\": 222.0}',0,'adm',0,'{\"2\": {\"id\": \"2\", \"nome\": \"6516516\", \"tipo\": \"unidade\", \"preco\": 111.0, \"desconto\": 0.0, \"acrescimo\": 0.0, \"nome_original\": \"6516516\", \"preco_original\": 111.0, \"quantidade_peso\": 2, \"preco_atacado_aplicado\": true, \"preco_promocional_aplicado\": false}}',NULL,'',0,'','','',0,0,'','2026-06-27 01:41:11','Balcão',0,'',0,'',0.00,'','finalizada','',NULL,'',0.0000,'',NULL,''),(4,4,'2026-06-26T22:53:26.841358','26/06/2026',1,'Consumidor Final',111,'{\"CartaoCredito\": 111.0, \"CartaoCredito_Bandeira\": \"\", \"CartaoCredito_ID\": \"\", \"CartaoCredito_Taxa\": 0.0, \"CartaoCredito_Taxa_Acrescimo_Ativo\": false, \"CartaoCredito_Valor_Original\": 111.0, \"CartaoCredito_Valor_Taxa\": 0.0, \"CartaoCredito_Parcelas\": 1, \"Parcelamento\": \"Cartao 1 Vez\"}',0,'adm',0,'{\"2\": {\"id\": \"2\", \"nome\": \"6516516\", \"tipo\": \"unidade\", \"preco\": 111.0, \"desconto\": 0.0, \"acrescimo\": 0.0, \"nome_original\": \"6516516\", \"preco_original\": 111.0, \"quantidade_peso\": 1, \"preco_atacado_aplicado\": true, \"preco_promocional_aplicado\": false}}',NULL,'',0,'','','',0,0,'','2026-06-27 01:53:30','Balcão',0,'',0,'',0.00,'','finalizada','',NULL,'',0.0000,'',NULL,''),(5,5,'2026-06-26T22:59:53.350983','26/06/2026',2,'mario silva',777,'{\"CartaoDebito\": 777.0, \"CartaoDebito_Bandeira\": \"\", \"CartaoDebito_ID\": \"\", \"CartaoDebito_Taxa\": 0.0, \"CartaoDebito_Taxa_Acrescimo_Ativo\": false, \"CartaoDebito_Valor_Original\": 777.0, \"CartaoDebito_Valor_Taxa\": 0.0, \"CartaoDebito_Parcelas\": 1, \"Parcelamento\": \"Cartao 1 Vez\"}',0,'adm',0,'{\"2\": {\"id\": \"2\", \"nome\": \"6516516\", \"tipo\": \"unidade\", \"preco\": 111.0, \"desconto\": 0.0, \"acrescimo\": 0.0, \"nome_original\": \"6516516\", \"preco_original\": 111.0, \"quantidade_peso\": 7, \"preco_atacado_aplicado\": true, \"preco_promocional_aplicado\": false}}',NULL,'',0,'','','',0,0,'','2026-06-27 02:00:01','Balcão',0,'',0,'',0.00,'','finalizada','',NULL,'',0.0000,'',NULL,''),(6,6,'2026-06-26T23:00:25.803880','26/06/2026',2,'mario silva',666,'{\"Dinheiro\": 607.1, \"CartaoDebito\": 58.9, \"CartaoDebito_Bandeira\": \"\", \"CartaoDebito_ID\": \"\", \"CartaoDebito_Taxa\": 0.0, \"CartaoDebito_Taxa_Acrescimo_Ativo\": false, \"CartaoDebito_Valor_Original\": 666.0, \"CartaoDebito_Valor_Taxa\": 0.0, \"CartaoDebito_Parcelas\": 1, \"Parcelamento\": \"Cartao 1 Vez\"}',0,'adm',0,'{\"2\": {\"id\": \"2\", \"nome\": \"6516516\", \"tipo\": \"unidade\", \"preco\": 111.0, \"desconto\": 0.0, \"acrescimo\": 0.0, \"nome_original\": \"6516516\", \"preco_original\": 111.0, \"quantidade_peso\": 6, \"preco_atacado_aplicado\": true, \"preco_promocional_aplicado\": false}}',NULL,'',0,'','','',0,0,'','2026-06-27 02:00:35','Balcão',0,'',0,'',0.00,'','finalizada','',NULL,'',0.0000,'',NULL,'');
/*!40000 ALTER TABLE `vendas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vendas_itens`
--

DROP TABLE IF EXISTS `vendas_itens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vendas_itens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `venda_id` int NOT NULL,
  `produto_id` int DEFAULT NULL,
  `codigo` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `produto_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `quantidade` decimal(15,3) DEFAULT '0.000',
  `valor_unitario` decimal(15,4) DEFAULT '0.0000',
  `valor_total` decimal(15,4) DEFAULT '0.0000',
  `lote` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `validade` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_validade` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `preco` decimal(15,2) DEFAULT '0.00',
  `preco_venda` decimal(15,2) DEFAULT '0.00',
  `tamanho` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tamanho_id` int DEFAULT NULL,
  `codigo_barras` varchar(160) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `unidade` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `preco_unitario` decimal(15,4) DEFAULT '0.0000',
  `subtotal` decimal(15,4) DEFAULT '0.0000',
  `produto` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `desconto` decimal(12,2) DEFAULT '0.00',
  PRIMARY KEY (`id`),
  KEY `idx_vendas_itens_venda` (`venda_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vendas_itens`
--

LOCK TABLES `vendas_itens` WRITE;
/*!40000 ALTER TABLE `vendas_itens` DISABLE KEYS */;
/*!40000 ALTER TABLE `vendas_itens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vendedores`
--

DROP TABLE IF EXISTS `vendedores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vendedores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `cpf` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `rg` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `telefone` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `telefone2` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `email` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `endereco` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `bairro` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `cidade` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `comissao` double DEFAULT '0',
  `meta_mensal` double DEFAULT '0',
  `salario_base` double DEFAULT '0',
  `pix` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `status` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Ativo',
  `data_admissao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_demissao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vendedores`
--

LOCK TABLES `vendedores` WRITE;
/*!40000 ALTER TABLE `vendedores` DISABLE KEYS */;
/*!40000 ALTER TABLE `vendedores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vinculos_usuario_caixa_turno`
--

DROP TABLE IF EXISTS `vinculos_usuario_caixa_turno`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vinculos_usuario_caixa_turno` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `caixa_id` int DEFAULT '0',
  `turno_id` int DEFAULT '0',
  `ativo` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vinculos_usuario_caixa_turno`
--

LOCK TABLES `vinculos_usuario_caixa_turno` WRITE;
/*!40000 ALTER TABLE `vinculos_usuario_caixa_turno` DISABLE KEYS */;
/*!40000 ALTER TABLE `vinculos_usuario_caixa_turno` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vouchers`
--

DROP TABLE IF EXISTS `vouchers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vouchers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `valor_original` double NOT NULL DEFAULT '0',
  `valor_restante` double NOT NULL DEFAULT '0',
  `cliente_id` int DEFAULT NULL,
  `cliente_nome` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `motivo` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `status` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT 'Ativo',
  `usuario_criacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `data_criacao` text COLLATE utf8mb4_unicode_ci,
  `data_utilizacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `venda_id` int DEFAULT NULL,
  `cupom_utilizado` int DEFAULT NULL,
  `observacao` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vouchers`
--

LOCK TABLES `vouchers` WRITE;
/*!40000 ALTER TABLE `vouchers` DISABLE KEYS */;
/*!40000 ALTER TABLE `vouchers` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-24 13:53:14
