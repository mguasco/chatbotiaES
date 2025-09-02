(function(){function r(e,n,t){function o(i,f){if(!n[i]){if(!e[i]){var c="function"==typeof require&&require;if(!f&&c)return c(i,!0);if(u)return u(i,!0);var a=new Error("Cannot find module '"+i+"'");throw a.code="MODULE_NOT_FOUND",a}var p=n[i]={exports:{}};e[i][0].call(p.exports,function(r){var n=e[i][1][r];return o(n||r)},p,p.exports,r,e,n,t)}return n[i].exports}for(var u="function"==typeof require&&require,i=0;i<t.length;i++)o(t[i]);return o}return r})()({1:[function(require,module,exports){
/*!
 * Lunr languages, `Spanish` language
 * https://github.com/MihaiValentin/lunr-languages
 *
 * Copyright 2014, Mihai Valentin
 * http://www.mozilla.org/MPL/
 */
/*!
 * based on
 * Snowball JavaScript Library v0.3
 * http://code.google.com/p/urim/
 * http://snowball.tartarus.org/
 *
 * Copyright 2010, Oleg Mazko
 * http://www.mozilla.org/MPL/
 */

/**
 * export the module via AMD, CommonJS or as a browser global
 * Export code from https://github.com/umdjs/umd/blob/master/returnExports.js
 */
;
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD. Register as an anonymous module.
    define(factory)
  } else if (typeof exports === 'object') {
    /**
     * Node. Does not work with strict CommonJS, but
     * only CommonJS-like environments that support module.exports,
     * like Node.
     */
    module.exports = factory()
  } else {
    // Browser globals (root is window)
    factory()(root.lunr);
  }
}(this, function() {
  /**
   * Just return a value to define the module export.
   * This example returns an object, but the module
   * can return a function as the exported value.
   */
  return function(lunr) {
    /* throw error if lunr is not yet included */
    if ('undefined' === typeof lunr) {
      throw new Error('Lunr is not present. Please include / require Lunr before this script.');
    }

    /* throw error if lunr stemmer support is not yet included */
    if ('undefined' === typeof lunr.stemmerSupport) {
      throw new Error('Lunr stemmer support is not present. Please include / require Lunr stemmer support before this script.');
    }

    /* register specific locale function */
    lunr.es = function() {
      this.pipeline.reset();
      this.pipeline.add(
        lunr.es.trimmer,
        lunr.es.stopWordFilter,
        lunr.es.stemmer
      );

      // for lunr version 2
      // this is necessary so that every searched word is also stemmed before
      // in lunr <= 1 this is not needed, as it is done using the normal pipeline
      if (this.searchPipeline) {
        this.searchPipeline.reset();
        this.searchPipeline.add(lunr.es.stemmer)
      }
    };

    /* lunr trimmer function */
    lunr.es.wordCharacters = "A-Za-z\xAA\xBA\xC0-\xD6\xD8-\xF6\xF8-\u02B8\u02E0-\u02E4\u1D00-\u1D25\u1D2C-\u1D5C\u1D62-\u1D65\u1D6B-\u1D77\u1D79-\u1DBE\u1E00-\u1EFF\u2071\u207F\u2090-\u209C\u212A\u212B\u2132\u214E\u2160-\u2188\u2C60-\u2C7F\uA722-\uA787\uA78B-\uA7AD\uA7B0-\uA7B7\uA7F7-\uA7FF\uAB30-\uAB5A\uAB5C-\uAB64\uFB00-\uFB06\uFF21-\uFF3A\uFF41-\uFF5A";
    lunr.es.trimmer = lunr.trimmerSupport.generateTrimmer(lunr.es.wordCharacters);

    lunr.Pipeline.registerFunction(lunr.es.trimmer, 'trimmer-es');

    /* lunr stemmer function */
    lunr.es.stemmer = (function() {
      /* create the wrapped stemmer object */
      var Among = lunr.stemmerSupport.Among,
        SnowballProgram = lunr.stemmerSupport.SnowballProgram,
        st = new function SpanishStemmer() {
          var a_0 = [new Among("", -1, 6), new Among("\u00E1", 0, 1),
              new Among("\u00E9", 0, 2), new Among("\u00ED", 0, 3),
              new Among("\u00F3", 0, 4), new Among("\u00FA", 0, 5)
            ],
            a_1 = [
              new Among("la", -1, -1), new Among("sela", 0, -1),
              new Among("le", -1, -1), new Among("me", -1, -1),
              new Among("se", -1, -1), new Among("lo", -1, -1),
              new Among("selo", 5, -1), new Among("las", -1, -1),
              new Among("selas", 7, -1), new Among("les", -1, -1),
              new Among("los", -1, -1), new Among("selos", 10, -1),
              new Among("nos", -1, -1)
            ],
            a_2 = [new Among("ando", -1, 6),
              new Among("iendo", -1, 6), new Among("yendo", -1, 7),
              new Among("\u00E1ndo", -1, 2), new Among("i\u00E9ndo", -1, 1),
              new Among("ar", -1, 6), new Among("er", -1, 6),
              new Among("ir", -1, 6), new Among("\u00E1r", -1, 3),
              new Among("\u00E9r", -1, 4), new Among("\u00EDr", -1, 5)
            ],
            a_3 = [
              new Among("ic", -1, -1), new Among("ad", -1, -1),
              new Among("os", -1, -1), new Among("iv", -1, 1)
            ],
            a_4 = [
              new Among("able", -1, 1), new Among("ible", -1, 1),
              new Among("ante", -1, 1)
            ],
            a_5 = [new Among("ic", -1, 1),
              new Among("abil", -1, 1), new Among("iv", -1, 1)
            ],
            a_6 = [
              new Among("ica", -1, 1), new Among("ancia", -1, 2),
              new Among("encia", -1, 5), new Among("adora", -1, 2),
              new Among("osa", -1, 1), new Among("ista", -1, 1),
              new Among("iva", -1, 9), new Among("anza", -1, 1),
              new Among("log\u00EDa", -1, 3), new Among("idad", -1, 8),
              new Among("able", -1, 1), new Among("ible", -1, 1),
              new Among("ante", -1, 2), new Among("mente", -1, 7),
              new Among("amente", 13, 6), new Among("aci\u00F3n", -1, 2),
              new Among("uci\u00F3n", -1, 4), new Among("ico", -1, 1),
              new Among("ismo", -1, 1), new Among("oso", -1, 1),
              new Among("amiento", -1, 1), new Among("imiento", -1, 1),
              new Among("ivo", -1, 9), new Among("ador", -1, 2),
              new Among("icas", -1, 1), new Among("ancias", -1, 2),
              new Among("encias", -1, 5), new Among("adoras", -1, 2),
              new Among("osas", -1, 1), new Among("istas", -1, 1),
              new Among("ivas", -1, 9), new Among("anzas", -1, 1),
              new Among("log\u00EDas", -1, 3), new Among("idades", -1, 8),
              new Among("ables", -1, 1), new Among("ibles", -1, 1),
              new Among("aciones", -1, 2), new Among("uciones", -1, 4),
              new Among("adores", -1, 2), new Among("antes", -1, 2),
              new Among("icos", -1, 1), new Among("ismos", -1, 1),
              new Among("osos", -1, 1), new Among("amientos", -1, 1),
              new Among("imientos", -1, 1), new Among("ivos", -1, 9)
            ],
            a_7 = [
              new Among("ya", -1, 1), new Among("ye", -1, 1),
              new Among("yan", -1, 1), new Among("yen", -1, 1),
              new Among("yeron", -1, 1), new Among("yendo", -1, 1),
              new Among("yo", -1, 1), new Among("yas", -1, 1),
              new Among("yes", -1, 1), new Among("yais", -1, 1),
              new Among("yamos", -1, 1), new Among("y\u00F3", -1, 1)
            ],
            a_8 = [
              new Among("aba", -1, 2), new Among("ada", -1, 2),
              new Among("ida", -1, 2), new Among("ara", -1, 2),
              new Among("iera", -1, 2), new Among("\u00EDa", -1, 2),
              new Among("ar\u00EDa", 5, 2), new Among("er\u00EDa", 5, 2),
              new Among("ir\u00EDa", 5, 2), new Among("ad", -1, 2),
              new Among("ed", -1, 2), new Among("id", -1, 2),
              new Among("ase", -1, 2), new Among("iese", -1, 2),
              new Among("aste", -1, 2), new Among("iste", -1, 2),
              new Among("an", -1, 2), new Among("aban", 16, 2),
              new Among("aran", 16, 2), new Among("ieran", 16, 2),
              new Among("\u00EDan", 16, 2), new Among("ar\u00EDan", 20, 2),
              new Among("er\u00EDan", 20, 2), new Among("ir\u00EDan", 20, 2),
              new Among("en", -1, 1), new Among("asen", 24, 2),
              new Among("iesen", 24, 2), new Among("aron", -1, 2),
              new Among("ieron", -1, 2), new Among("ar\u00E1n", -1, 2),
              new Among("er\u00E1n", -1, 2), new Among("ir\u00E1n", -1, 2),
              new Among("ado", -1, 2), new Among("ido", -1, 2),
              new Among("ando", -1, 2), new Among("iendo", -1, 2),
              new Among("ar", -1, 2), new Among("er", -1, 2),
              new Among("ir", -1, 2), new Among("as", -1, 2),
              new Among("abas", 39, 2), new Among("adas", 39, 2),
              new Among("idas", 39, 2), new Among("aras", 39, 2),
              new Among("ieras", 39, 2), new Among("\u00EDas", 39, 2),
              new Among("ar\u00EDas", 45, 2), new Among("er\u00EDas", 45, 2),
              new Among("ir\u00EDas", 45, 2), new Among("es", -1, 1),
              new Among("ases", 49, 2), new Among("ieses", 49, 2),
              new Among("abais", -1, 2), new Among("arais", -1, 2),
              new Among("ierais", -1, 2), new Among("\u00EDais", -1, 2),
              new Among("ar\u00EDais", 55, 2), new Among("er\u00EDais", 55, 2),
              new Among("ir\u00EDais", 55, 2), new Among("aseis", -1, 2),
              new Among("ieseis", -1, 2), new Among("asteis", -1, 2),
              new Among("isteis", -1, 2), new Among("\u00E1is", -1, 2),
              new Among("\u00E9is", -1, 1), new Among("ar\u00E9is", 64, 2),
              new Among("er\u00E9is", 64, 2), new Among("ir\u00E9is", 64, 2),
              new Among("ados", -1, 2), new Among("idos", -1, 2),
              new Among("amos", -1, 2), new Among("\u00E1bamos", 70, 2),
              new Among("\u00E1ramos", 70, 2), new Among("i\u00E9ramos", 70, 2),
              new Among("\u00EDamos", 70, 2), new Among("ar\u00EDamos", 74, 2),
              new Among("er\u00EDamos", 74, 2), new Among("ir\u00EDamos", 74, 2),
              new Among("emos", -1, 1), new Among("aremos", 78, 2),
              new Among("eremos", 78, 2), new Among("iremos", 78, 2),
              new Among("\u00E1semos", 78, 2), new Among("i\u00E9semos", 78, 2),
              new Among("imos", -1, 2), new Among("ar\u00E1s", -1, 2),
              new Among("er\u00E1s", -1, 2), new Among("ir\u00E1s", -1, 2),
              new Among("\u00EDs", -1, 2), new Among("ar\u00E1", -1, 2),
              new Among("er\u00E1", -1, 2), new Among("ir\u00E1", -1, 2),
              new Among("ar\u00E9", -1, 2), new Among("er\u00E9", -1, 2),
              new Among("ir\u00E9", -1, 2), new Among("i\u00F3", -1, 2)
            ],
            a_9 = [
              new Among("a", -1, 1), new Among("e", -1, 2),
              new Among("o", -1, 1), new Among("os", -1, 1),
              new Among("\u00E1", -1, 1), new Among("\u00E9", -1, 2),
              new Among("\u00ED", -1, 1), new Among("\u00F3", -1, 1)
            ],
            g_v = [17,
              65, 16, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 17, 4, 10
            ],
            I_p2, I_p1, I_pV, sbp = new SnowballProgram();
          this.setCurrent = function(word) {
            sbp.setCurrent(word);
          };
          this.getCurrent = function() {
            return sbp.getCurrent();
          };

          function habr1() {
            if (sbp.out_grouping(g_v, 97, 252)) {
              while (!sbp.in_grouping(g_v, 97, 252)) {
                if (sbp.cursor >= sbp.limit)
                  return true;
                sbp.cursor++;
              }
              return false;
            }
            return true;
          }

          function habr2() {
            if (sbp.in_grouping(g_v, 97, 252)) {
              var v_1 = sbp.cursor;
              if (habr1()) {
                sbp.cursor = v_1;
                if (!sbp.in_grouping(g_v, 97, 252))
                  return true;
                while (!sbp.out_grouping(g_v, 97, 252)) {
                  if (sbp.cursor >= sbp.limit)
                    return true;
                  sbp.cursor++;
                }
              }
              return false;
            }
            return true;
          }

          function habr3() {
            var v_1 = sbp.cursor,
              v_2;
            if (habr2()) {
              sbp.cursor = v_1;
              if (!sbp.out_grouping(g_v, 97, 252))
                return;
              v_2 = sbp.cursor;
              if (habr1()) {
                sbp.cursor = v_2;
                if (!sbp.in_grouping(g_v, 97, 252) || sbp.cursor >= sbp.limit)
                  return;
                sbp.cursor++;
              }
            }
            I_pV = sbp.cursor;
          }

          function habr4() {
            while (!sbp.in_grouping(g_v, 97, 252)) {
              if (sbp.cursor >= sbp.limit)
                return false;
              sbp.cursor++;
            }
            while (!sbp.out_grouping(g_v, 97, 252)) {
              if (sbp.cursor >= sbp.limit)
                return false;
              sbp.cursor++;
            }
            return true;
          }

          function r_mark_regions() {
            var v_1 = sbp.cursor;
            I_pV = sbp.limit;
            I_p1 = I_pV;
            I_p2 = I_pV;
            habr3();
            sbp.cursor = v_1;
            if (habr4()) {
              I_p1 = sbp.cursor;
              if (habr4())
                I_p2 = sbp.cursor;
            }
          }

          function r_postlude() {
            var among_var;
            while (true) {
              sbp.bra = sbp.cursor;
              among_var = sbp.find_among(a_0, 6);
              if (among_var) {
                sbp.ket = sbp.cursor;
                switch (among_var) {
                  case 1:
                    sbp.slice_from("a");
                    continue;
                  case 2:
                    sbp.slice_from("e");
                    continue;
                  case 3:
                    sbp.slice_from("i");
                    continue;
                  case 4:
                    sbp.slice_from("o");
                    continue;
                  case 5:
                    sbp.slice_from("u");
                    continue;
                  case 6:
                    if (sbp.cursor >= sbp.limit)
                      break;
                    sbp.cursor++;
                    continue;
                }
              }
              break;
            }
          }

          function r_RV() {
            return I_pV <= sbp.cursor;
          }

          function r_R1() {
            return I_p1 <= sbp.cursor;
          }

          function r_R2() {
            return I_p2 <= sbp.cursor;
          }

          function r_attached_pronoun() {
            var among_var;
            sbp.ket = sbp.cursor;
            if (sbp.find_among_b(a_1, 13)) {
              sbp.bra = sbp.cursor;
              among_var = sbp.find_among_b(a_2, 11);
              if (among_var && r_RV())
                switch (among_var) {
                  case 1:
                    sbp.bra = sbp.cursor;
                    sbp.slice_from("iendo");
                    break;
                  case 2:
                    sbp.bra = sbp.cursor;
                    sbp.slice_from("ando");
                    break;
                  case 3:
                    sbp.bra = sbp.cursor;
                    sbp.slice_from("ar");
                    break;
                  case 4:
                    sbp.bra = sbp.cursor;
                    sbp.slice_from("er");
                    break;
                  case 5:
                    sbp.bra = sbp.cursor;
                    sbp.slice_from("ir");
                    break;
                  case 6:
                    sbp.slice_del();
                    break;
                  case 7:
                    if (sbp.eq_s_b(1, "u"))
                      sbp.slice_del();
                    break;
                }
            }
          }

          function habr5(a, n) {
            if (!r_R2())
              return true;
            sbp.slice_del();
            sbp.ket = sbp.cursor;
            var among_var = sbp.find_among_b(a, n);
            if (among_var) {
              sbp.bra = sbp.cursor;
              if (among_var == 1 && r_R2())
                sbp.slice_del();
            }
            return false;
          }

          function habr6(c1) {
            if (!r_R2())
              return true;
            sbp.slice_del();
            sbp.ket = sbp.cursor;
            if (sbp.eq_s_b(2, c1)) {
              sbp.bra = sbp.cursor;
              if (r_R2())
                sbp.slice_del();
            }
            return false;
          }

          function r_standard_suffix() {
            var among_var;
            sbp.ket = sbp.cursor;
            among_var = sbp.find_among_b(a_6, 46);
            if (among_var) {
              sbp.bra = sbp.cursor;
              switch (among_var) {
                case 1:
                  if (!r_R2())
                    return false;
                  sbp.slice_del();
                  break;
                case 2:
                  if (habr6("ic"))
                    return false;
                  break;
                case 3:
                  if (!r_R2())
                    return false;
                  sbp.slice_from("log");
                  break;
                case 4:
                  if (!r_R2())
                    return false;
                  sbp.slice_from("u");
                  break;
                case 5:
                  if (!r_R2())
                    return false;
                  sbp.slice_from("ente");
                  break;
                case 6:
                  if (!r_R1())
                    return false;
                  sbp.slice_del();
                  sbp.ket = sbp.cursor;
                  among_var = sbp.find_among_b(a_3, 4);
                  if (among_var) {
                    sbp.bra = sbp.cursor;
                    if (r_R2()) {
                      sbp.slice_del();
                      if (among_var == 1) {
                        sbp.ket = sbp.cursor;
                        if (sbp.eq_s_b(2, "at")) {
                          sbp.bra = sbp.cursor;
                          if (r_R2())
                            sbp.slice_del();
                        }
                      }
                    }
                  }
                  break;
                case 7:
                  if (habr5(a_4, 3))
                    return false;
                  break;
                case 8:
                  if (habr5(a_5, 3))
                    return false;
                  break;
                case 9:
                  if (habr6("at"))
                    return false;
                  break;
              }
              return true;
            }
            return false;
          }

          function r_y_verb_suffix() {
            var among_var, v_1;
            if (sbp.cursor >= I_pV) {
              v_1 = sbp.limit_backward;
              sbp.limit_backward = I_pV;
              sbp.ket = sbp.cursor;
              among_var = sbp.find_among_b(a_7, 12);
              sbp.limit_backward = v_1;
              if (among_var) {
                sbp.bra = sbp.cursor;
                if (among_var == 1) {
                  if (!sbp.eq_s_b(1, "u"))
                    return false;
                  sbp.slice_del();
                }
                return true;
              }
            }
            return false;
          }

          function r_verb_suffix() {
            var among_var, v_1, v_2, v_3;
            if (sbp.cursor >= I_pV) {
              v_1 = sbp.limit_backward;
              sbp.limit_backward = I_pV;
              sbp.ket = sbp.cursor;
              among_var = sbp.find_among_b(a_8, 96);
              sbp.limit_backward = v_1;
              if (among_var) {
                sbp.bra = sbp.cursor;
                switch (among_var) {
                  case 1:
                    v_2 = sbp.limit - sbp.cursor;
                    if (sbp.eq_s_b(1, "u")) {
                      v_3 = sbp.limit - sbp.cursor;
                      if (sbp.eq_s_b(1, "g"))
                        sbp.cursor = sbp.limit - v_3;
                      else
                        sbp.cursor = sbp.limit - v_2;
                    } else
                      sbp.cursor = sbp.limit - v_2;
                    sbp.bra = sbp.cursor;
                  case 2:
                    sbp.slice_del();
                    break;
                }
              }
            }
          }

          function r_residual_suffix() {
            var among_var, v_1;
            sbp.ket = sbp.cursor;
            among_var = sbp.find_among_b(a_9, 8);
            if (among_var) {
              sbp.bra = sbp.cursor;
              switch (among_var) {
                case 1:
                  if (r_RV())
                    sbp.slice_del();
                  break;
                case 2:
                  if (r_RV()) {
                    sbp.slice_del();
                    sbp.ket = sbp.cursor;
                    if (sbp.eq_s_b(1, "u")) {
                      sbp.bra = sbp.cursor;
                      v_1 = sbp.limit - sbp.cursor;
                      if (sbp.eq_s_b(1, "g")) {
                        sbp.cursor = sbp.limit - v_1;
                        if (r_RV())
                          sbp.slice_del();
                      }
                    }
                  }
                  break;
              }
            }
          }
          this.stem = function() {
            var v_1 = sbp.cursor;
            r_mark_regions();
            sbp.limit_backward = v_1;
            sbp.cursor = sbp.limit;
            r_attached_pronoun();
            sbp.cursor = sbp.limit;
            if (!r_standard_suffix()) {
              sbp.cursor = sbp.limit;
              if (!r_y_verb_suffix()) {
                sbp.cursor = sbp.limit;
                r_verb_suffix();
              }
            }
            sbp.cursor = sbp.limit;
            r_residual_suffix();
            sbp.cursor = sbp.limit_backward;
            r_postlude();
            return true;
          }
        };

      /* and return a function that stems a word for the current locale */
      return function(token) {
        // for lunr version 2
        if (typeof token.update === "function") {
          return token.update(function(word) {
            st.setCurrent(word);
            st.stem();
            return st.getCurrent();
          })
        } else { // for lunr version <= 1
          st.setCurrent(token);
          st.stem();
          return st.getCurrent();
        }
      }
    })();

    lunr.Pipeline.registerFunction(lunr.es.stemmer, 'stemmer-es');

    lunr.es.stopWordFilter = lunr.generateStopWordFilter('a al algo algunas algunos ante antes como con contra cual cuando de del desde donde durante e el ella ellas ellos en entre era erais eran eras eres es esa esas ese eso esos esta estaba estabais estaban estabas estad estada estadas estado estados estamos estando estar estaremos estará estarán estarás estaré estaréis estaría estaríais estaríamos estarían estarías estas este estemos esto estos estoy estuve estuviera estuvierais estuvieran estuvieras estuvieron estuviese estuvieseis estuviesen estuvieses estuvimos estuviste estuvisteis estuviéramos estuviésemos estuvo está estábamos estáis están estás esté estéis estén estés fue fuera fuerais fueran fueras fueron fuese fueseis fuesen fueses fui fuimos fuiste fuisteis fuéramos fuésemos ha habida habidas habido habidos habiendo habremos habrá habrán habrás habré habréis habría habríais habríamos habrían habrías habéis había habíais habíamos habían habías han has hasta hay haya hayamos hayan hayas hayáis he hemos hube hubiera hubierais hubieran hubieras hubieron hubiese hubieseis hubiesen hubieses hubimos hubiste hubisteis hubiéramos hubiésemos hubo la las le les lo los me mi mis mucho muchos muy más mí mía mías mío míos nada ni no nos nosotras nosotros nuestra nuestras nuestro nuestros o os otra otras otro otros para pero poco por porque que quien quienes qué se sea seamos sean seas seremos será serán serás seré seréis sería seríais seríamos serían serías seáis sido siendo sin sobre sois somos son soy su sus suya suyas suyo suyos sí también tanto te tendremos tendrá tendrán tendrás tendré tendréis tendría tendríais tendríamos tendrían tendrías tened tenemos tenga tengamos tengan tengas tengo tengáis tenida tenidas tenido tenidos teniendo tenéis tenía teníais teníamos tenían tenías ti tiene tienen tienes todo todos tu tus tuve tuviera tuvierais tuvieran tuvieras tuvieron tuviese tuvieseis tuviesen tuvieses tuvimos tuviste tuvisteis tuviéramos tuviésemos tuvo tuya tuyas tuyo tuyos tú un una uno unos vosotras vosotros vuestra vuestras vuestro vuestros y ya yo él éramos'.split(' '));

    lunr.Pipeline.registerFunction(lunr.es.stopWordFilter, 'stopWordFilter-es');
  };
}))
},{}],2:[function(require,module,exports){
(function (global){
'use strict';

var rh = global.rh;
var lunrlang = require('../../node_modules/lunr-languages/lunr.es');
rh._.exports(lunrlang);

}).call(this,typeof global !== "undefined" ? global : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : {})

},{"../../node_modules/lunr-languages/lunr.es":1}]},{},[2])
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIm5vZGVfbW9kdWxlcy9icm93c2VyLXBhY2svX3ByZWx1ZGUuanMiLCJub2RlX21vZHVsZXMvbHVuci1sYW5ndWFnZXMvbHVuci5lcy5qcyIsInNyYy9sYW5ndWFnZXMvZXMuanM2Il0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUFBO0FDQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7Ozs7QUN0bEJBLElBQUksS0FBSyxPQUFPLEVBQWhCO0FBQ0EsSUFBSSxXQUFXLFFBQVEsMkNBQVIsQ0FBZjtBQUNBLEdBQUcsQ0FBSCxDQUFLLE9BQUwsQ0FBYyxRQUFkIiwiZmlsZSI6ImdlbmVyYXRlZC5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzQ29udGVudCI6WyIoZnVuY3Rpb24oKXtmdW5jdGlvbiByKGUsbix0KXtmdW5jdGlvbiBvKGksZil7aWYoIW5baV0pe2lmKCFlW2ldKXt2YXIgYz1cImZ1bmN0aW9uXCI9PXR5cGVvZiByZXF1aXJlJiZyZXF1aXJlO2lmKCFmJiZjKXJldHVybiBjKGksITApO2lmKHUpcmV0dXJuIHUoaSwhMCk7dmFyIGE9bmV3IEVycm9yKFwiQ2Fubm90IGZpbmQgbW9kdWxlICdcIitpK1wiJ1wiKTt0aHJvdyBhLmNvZGU9XCJNT0RVTEVfTk9UX0ZPVU5EXCIsYX12YXIgcD1uW2ldPXtleHBvcnRzOnt9fTtlW2ldWzBdLmNhbGwocC5leHBvcnRzLGZ1bmN0aW9uKHIpe3ZhciBuPWVbaV1bMV1bcl07cmV0dXJuIG8obnx8cil9LHAscC5leHBvcnRzLHIsZSxuLHQpfXJldHVybiBuW2ldLmV4cG9ydHN9Zm9yKHZhciB1PVwiZnVuY3Rpb25cIj09dHlwZW9mIHJlcXVpcmUmJnJlcXVpcmUsaT0wO2k8dC5sZW5ndGg7aSsrKW8odFtpXSk7cmV0dXJuIG99cmV0dXJuIHJ9KSgpIiwiLyohXG4gKiBMdW5yIGxhbmd1YWdlcywgYFNwYW5pc2hgIGxhbmd1YWdlXG4gKiBodHRwczovL2dpdGh1Yi5jb20vTWloYWlWYWxlbnRpbi9sdW5yLWxhbmd1YWdlc1xuICpcbiAqIENvcHlyaWdodCAyMDE0LCBNaWhhaSBWYWxlbnRpblxuICogaHR0cDovL3d3dy5tb3ppbGxhLm9yZy9NUEwvXG4gKi9cbi8qIVxuICogYmFzZWQgb25cbiAqIFNub3diYWxsIEphdmFTY3JpcHQgTGlicmFyeSB2MC4zXG4gKiBodHRwOi8vY29kZS5nb29nbGUuY29tL3AvdXJpbS9cbiAqIGh0dHA6Ly9zbm93YmFsbC50YXJ0YXJ1cy5vcmcvXG4gKlxuICogQ29weXJpZ2h0IDIwMTAsIE9sZWcgTWF6a29cbiAqIGh0dHA6Ly93d3cubW96aWxsYS5vcmcvTVBML1xuICovXG5cbi8qKlxuICogZXhwb3J0IHRoZSBtb2R1bGUgdmlhIEFNRCwgQ29tbW9uSlMgb3IgYXMgYSBicm93c2VyIGdsb2JhbFxuICogRXhwb3J0IGNvZGUgZnJvbSBodHRwczovL2dpdGh1Yi5jb20vdW1kanMvdW1kL2Jsb2IvbWFzdGVyL3JldHVybkV4cG9ydHMuanNcbiAqL1xuO1xuKGZ1bmN0aW9uKHJvb3QsIGZhY3RvcnkpIHtcbiAgaWYgKHR5cGVvZiBkZWZpbmUgPT09ICdmdW5jdGlvbicgJiYgZGVmaW5lLmFtZCkge1xuICAgIC8vIEFNRC4gUmVnaXN0ZXIgYXMgYW4gYW5vbnltb3VzIG1vZHVsZS5cbiAgICBkZWZpbmUoZmFjdG9yeSlcbiAgfSBlbHNlIGlmICh0eXBlb2YgZXhwb3J0cyA9PT0gJ29iamVjdCcpIHtcbiAgICAvKipcbiAgICAgKiBOb2RlLiBEb2VzIG5vdCB3b3JrIHdpdGggc3RyaWN0IENvbW1vbkpTLCBidXRcbiAgICAgKiBvbmx5IENvbW1vbkpTLWxpa2UgZW52aXJvbm1lbnRzIHRoYXQgc3VwcG9ydCBtb2R1bGUuZXhwb3J0cyxcbiAgICAgKiBsaWtlIE5vZGUuXG4gICAgICovXG4gICAgbW9kdWxlLmV4cG9ydHMgPSBmYWN0b3J5KClcbiAgfSBlbHNlIHtcbiAgICAvLyBCcm93c2VyIGdsb2JhbHMgKHJvb3QgaXMgd2luZG93KVxuICAgIGZhY3RvcnkoKShyb290Lmx1bnIpO1xuICB9XG59KHRoaXMsIGZ1bmN0aW9uKCkge1xuICAvKipcbiAgICogSnVzdCByZXR1cm4gYSB2YWx1ZSB0byBkZWZpbmUgdGhlIG1vZHVsZSBleHBvcnQuXG4gICAqIFRoaXMgZXhhbXBsZSByZXR1cm5zIGFuIG9iamVjdCwgYnV0IHRoZSBtb2R1bGVcbiAgICogY2FuIHJldHVybiBhIGZ1bmN0aW9uIGFzIHRoZSBleHBvcnRlZCB2YWx1ZS5cbiAgICovXG4gIHJldHVybiBmdW5jdGlvbihsdW5yKSB7XG4gICAgLyogdGhyb3cgZXJyb3IgaWYgbHVuciBpcyBub3QgeWV0IGluY2x1ZGVkICovXG4gICAgaWYgKCd1bmRlZmluZWQnID09PSB0eXBlb2YgbHVucikge1xuICAgICAgdGhyb3cgbmV3IEVycm9yKCdMdW5yIGlzIG5vdCBwcmVzZW50LiBQbGVhc2UgaW5jbHVkZSAvIHJlcXVpcmUgTHVuciBiZWZvcmUgdGhpcyBzY3JpcHQuJyk7XG4gICAgfVxuXG4gICAgLyogdGhyb3cgZXJyb3IgaWYgbHVuciBzdGVtbWVyIHN1cHBvcnQgaXMgbm90IHlldCBpbmNsdWRlZCAqL1xuICAgIGlmICgndW5kZWZpbmVkJyA9PT0gdHlwZW9mIGx1bnIuc3RlbW1lclN1cHBvcnQpIHtcbiAgICAgIHRocm93IG5ldyBFcnJvcignTHVuciBzdGVtbWVyIHN1cHBvcnQgaXMgbm90IHByZXNlbnQuIFBsZWFzZSBpbmNsdWRlIC8gcmVxdWlyZSBMdW5yIHN0ZW1tZXIgc3VwcG9ydCBiZWZvcmUgdGhpcyBzY3JpcHQuJyk7XG4gICAgfVxuXG4gICAgLyogcmVnaXN0ZXIgc3BlY2lmaWMgbG9jYWxlIGZ1bmN0aW9uICovXG4gICAgbHVuci5lcyA9IGZ1bmN0aW9uKCkge1xuICAgICAgdGhpcy5waXBlbGluZS5yZXNldCgpO1xuICAgICAgdGhpcy5waXBlbGluZS5hZGQoXG4gICAgICAgIGx1bnIuZXMudHJpbW1lcixcbiAgICAgICAgbHVuci5lcy5zdG9wV29yZEZpbHRlcixcbiAgICAgICAgbHVuci5lcy5zdGVtbWVyXG4gICAgICApO1xuXG4gICAgICAvLyBmb3IgbHVuciB2ZXJzaW9uIDJcbiAgICAgIC8vIHRoaXMgaXMgbmVjZXNzYXJ5IHNvIHRoYXQgZXZlcnkgc2VhcmNoZWQgd29yZCBpcyBhbHNvIHN0ZW1tZWQgYmVmb3JlXG4gICAgICAvLyBpbiBsdW5yIDw9IDEgdGhpcyBpcyBub3QgbmVlZGVkLCBhcyBpdCBpcyBkb25lIHVzaW5nIHRoZSBub3JtYWwgcGlwZWxpbmVcbiAgICAgIGlmICh0aGlzLnNlYXJjaFBpcGVsaW5lKSB7XG4gICAgICAgIHRoaXMuc2VhcmNoUGlwZWxpbmUucmVzZXQoKTtcbiAgICAgICAgdGhpcy5zZWFyY2hQaXBlbGluZS5hZGQobHVuci5lcy5zdGVtbWVyKVxuICAgICAgfVxuICAgIH07XG5cbiAgICAvKiBsdW5yIHRyaW1tZXIgZnVuY3Rpb24gKi9cbiAgICBsdW5yLmVzLndvcmRDaGFyYWN0ZXJzID0gXCJBLVphLXpcXHhBQVxceEJBXFx4QzAtXFx4RDZcXHhEOC1cXHhGNlxceEY4LVxcdTAyQjhcXHUwMkUwLVxcdTAyRTRcXHUxRDAwLVxcdTFEMjVcXHUxRDJDLVxcdTFENUNcXHUxRDYyLVxcdTFENjVcXHUxRDZCLVxcdTFENzdcXHUxRDc5LVxcdTFEQkVcXHUxRTAwLVxcdTFFRkZcXHUyMDcxXFx1MjA3RlxcdTIwOTAtXFx1MjA5Q1xcdTIxMkFcXHUyMTJCXFx1MjEzMlxcdTIxNEVcXHUyMTYwLVxcdTIxODhcXHUyQzYwLVxcdTJDN0ZcXHVBNzIyLVxcdUE3ODdcXHVBNzhCLVxcdUE3QURcXHVBN0IwLVxcdUE3QjdcXHVBN0Y3LVxcdUE3RkZcXHVBQjMwLVxcdUFCNUFcXHVBQjVDLVxcdUFCNjRcXHVGQjAwLVxcdUZCMDZcXHVGRjIxLVxcdUZGM0FcXHVGRjQxLVxcdUZGNUFcIjtcbiAgICBsdW5yLmVzLnRyaW1tZXIgPSBsdW5yLnRyaW1tZXJTdXBwb3J0LmdlbmVyYXRlVHJpbW1lcihsdW5yLmVzLndvcmRDaGFyYWN0ZXJzKTtcblxuICAgIGx1bnIuUGlwZWxpbmUucmVnaXN0ZXJGdW5jdGlvbihsdW5yLmVzLnRyaW1tZXIsICd0cmltbWVyLWVzJyk7XG5cbiAgICAvKiBsdW5yIHN0ZW1tZXIgZnVuY3Rpb24gKi9cbiAgICBsdW5yLmVzLnN0ZW1tZXIgPSAoZnVuY3Rpb24oKSB7XG4gICAgICAvKiBjcmVhdGUgdGhlIHdyYXBwZWQgc3RlbW1lciBvYmplY3QgKi9cbiAgICAgIHZhciBBbW9uZyA9IGx1bnIuc3RlbW1lclN1cHBvcnQuQW1vbmcsXG4gICAgICAgIFNub3diYWxsUHJvZ3JhbSA9IGx1bnIuc3RlbW1lclN1cHBvcnQuU25vd2JhbGxQcm9ncmFtLFxuICAgICAgICBzdCA9IG5ldyBmdW5jdGlvbiBTcGFuaXNoU3RlbW1lcigpIHtcbiAgICAgICAgICB2YXIgYV8wID0gW25ldyBBbW9uZyhcIlwiLCAtMSwgNiksIG5ldyBBbW9uZyhcIlxcdTAwRTFcIiwgMCwgMSksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcIlxcdTAwRTlcIiwgMCwgMiksIG5ldyBBbW9uZyhcIlxcdTAwRURcIiwgMCwgMyksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcIlxcdTAwRjNcIiwgMCwgNCksIG5ldyBBbW9uZyhcIlxcdTAwRkFcIiwgMCwgNSlcbiAgICAgICAgICAgIF0sXG4gICAgICAgICAgICBhXzEgPSBbXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImxhXCIsIC0xLCAtMSksIG5ldyBBbW9uZyhcInNlbGFcIiwgMCwgLTEpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJsZVwiLCAtMSwgLTEpLCBuZXcgQW1vbmcoXCJtZVwiLCAtMSwgLTEpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJzZVwiLCAtMSwgLTEpLCBuZXcgQW1vbmcoXCJsb1wiLCAtMSwgLTEpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJzZWxvXCIsIDUsIC0xKSwgbmV3IEFtb25nKFwibGFzXCIsIC0xLCAtMSksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcInNlbGFzXCIsIDcsIC0xKSwgbmV3IEFtb25nKFwibGVzXCIsIC0xLCAtMSksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImxvc1wiLCAtMSwgLTEpLCBuZXcgQW1vbmcoXCJzZWxvc1wiLCAxMCwgLTEpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJub3NcIiwgLTEsIC0xKVxuICAgICAgICAgICAgXSxcbiAgICAgICAgICAgIGFfMiA9IFtuZXcgQW1vbmcoXCJhbmRvXCIsIC0xLCA2KSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiaWVuZG9cIiwgLTEsIDYpLCBuZXcgQW1vbmcoXCJ5ZW5kb1wiLCAtMSwgNyksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcIlxcdTAwRTFuZG9cIiwgLTEsIDIpLCBuZXcgQW1vbmcoXCJpXFx1MDBFOW5kb1wiLCAtMSwgMSksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImFyXCIsIC0xLCA2KSwgbmV3IEFtb25nKFwiZXJcIiwgLTEsIDYpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJpclwiLCAtMSwgNiksIG5ldyBBbW9uZyhcIlxcdTAwRTFyXCIsIC0xLCAzKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiXFx1MDBFOXJcIiwgLTEsIDQpLCBuZXcgQW1vbmcoXCJcXHUwMEVEclwiLCAtMSwgNSlcbiAgICAgICAgICAgIF0sXG4gICAgICAgICAgICBhXzMgPSBbXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImljXCIsIC0xLCAtMSksIG5ldyBBbW9uZyhcImFkXCIsIC0xLCAtMSksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcIm9zXCIsIC0xLCAtMSksIG5ldyBBbW9uZyhcIml2XCIsIC0xLCAxKVxuICAgICAgICAgICAgXSxcbiAgICAgICAgICAgIGFfNCA9IFtcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiYWJsZVwiLCAtMSwgMSksIG5ldyBBbW9uZyhcImlibGVcIiwgLTEsIDEpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJhbnRlXCIsIC0xLCAxKVxuICAgICAgICAgICAgXSxcbiAgICAgICAgICAgIGFfNSA9IFtuZXcgQW1vbmcoXCJpY1wiLCAtMSwgMSksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImFiaWxcIiwgLTEsIDEpLCBuZXcgQW1vbmcoXCJpdlwiLCAtMSwgMSlcbiAgICAgICAgICAgIF0sXG4gICAgICAgICAgICBhXzYgPSBbXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImljYVwiLCAtMSwgMSksIG5ldyBBbW9uZyhcImFuY2lhXCIsIC0xLCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiZW5jaWFcIiwgLTEsIDUpLCBuZXcgQW1vbmcoXCJhZG9yYVwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcIm9zYVwiLCAtMSwgMSksIG5ldyBBbW9uZyhcImlzdGFcIiwgLTEsIDEpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJpdmFcIiwgLTEsIDkpLCBuZXcgQW1vbmcoXCJhbnphXCIsIC0xLCAxKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwibG9nXFx1MDBFRGFcIiwgLTEsIDMpLCBuZXcgQW1vbmcoXCJpZGFkXCIsIC0xLCA4KSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiYWJsZVwiLCAtMSwgMSksIG5ldyBBbW9uZyhcImlibGVcIiwgLTEsIDEpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJhbnRlXCIsIC0xLCAyKSwgbmV3IEFtb25nKFwibWVudGVcIiwgLTEsIDcpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJhbWVudGVcIiwgMTMsIDYpLCBuZXcgQW1vbmcoXCJhY2lcXHUwMEYzblwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcInVjaVxcdTAwRjNuXCIsIC0xLCA0KSwgbmV3IEFtb25nKFwiaWNvXCIsIC0xLCAxKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiaXNtb1wiLCAtMSwgMSksIG5ldyBBbW9uZyhcIm9zb1wiLCAtMSwgMSksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImFtaWVudG9cIiwgLTEsIDEpLCBuZXcgQW1vbmcoXCJpbWllbnRvXCIsIC0xLCAxKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiaXZvXCIsIC0xLCA5KSwgbmV3IEFtb25nKFwiYWRvclwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImljYXNcIiwgLTEsIDEpLCBuZXcgQW1vbmcoXCJhbmNpYXNcIiwgLTEsIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJlbmNpYXNcIiwgLTEsIDUpLCBuZXcgQW1vbmcoXCJhZG9yYXNcIiwgLTEsIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJvc2FzXCIsIC0xLCAxKSwgbmV3IEFtb25nKFwiaXN0YXNcIiwgLTEsIDEpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJpdmFzXCIsIC0xLCA5KSwgbmV3IEFtb25nKFwiYW56YXNcIiwgLTEsIDEpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJsb2dcXHUwMEVEYXNcIiwgLTEsIDMpLCBuZXcgQW1vbmcoXCJpZGFkZXNcIiwgLTEsIDgpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJhYmxlc1wiLCAtMSwgMSksIG5ldyBBbW9uZyhcImlibGVzXCIsIC0xLCAxKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiYWNpb25lc1wiLCAtMSwgMiksIG5ldyBBbW9uZyhcInVjaW9uZXNcIiwgLTEsIDQpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJhZG9yZXNcIiwgLTEsIDIpLCBuZXcgQW1vbmcoXCJhbnRlc1wiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImljb3NcIiwgLTEsIDEpLCBuZXcgQW1vbmcoXCJpc21vc1wiLCAtMSwgMSksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcIm9zb3NcIiwgLTEsIDEpLCBuZXcgQW1vbmcoXCJhbWllbnRvc1wiLCAtMSwgMSksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImltaWVudG9zXCIsIC0xLCAxKSwgbmV3IEFtb25nKFwiaXZvc1wiLCAtMSwgOSlcbiAgICAgICAgICAgIF0sXG4gICAgICAgICAgICBhXzcgPSBbXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcInlhXCIsIC0xLCAxKSwgbmV3IEFtb25nKFwieWVcIiwgLTEsIDEpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJ5YW5cIiwgLTEsIDEpLCBuZXcgQW1vbmcoXCJ5ZW5cIiwgLTEsIDEpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJ5ZXJvblwiLCAtMSwgMSksIG5ldyBBbW9uZyhcInllbmRvXCIsIC0xLCAxKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwieW9cIiwgLTEsIDEpLCBuZXcgQW1vbmcoXCJ5YXNcIiwgLTEsIDEpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJ5ZXNcIiwgLTEsIDEpLCBuZXcgQW1vbmcoXCJ5YWlzXCIsIC0xLCAxKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwieWFtb3NcIiwgLTEsIDEpLCBuZXcgQW1vbmcoXCJ5XFx1MDBGM1wiLCAtMSwgMSlcbiAgICAgICAgICAgIF0sXG4gICAgICAgICAgICBhXzggPSBbXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImFiYVwiLCAtMSwgMiksIG5ldyBBbW9uZyhcImFkYVwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImlkYVwiLCAtMSwgMiksIG5ldyBBbW9uZyhcImFyYVwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImllcmFcIiwgLTEsIDIpLCBuZXcgQW1vbmcoXCJcXHUwMEVEYVwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImFyXFx1MDBFRGFcIiwgNSwgMiksIG5ldyBBbW9uZyhcImVyXFx1MDBFRGFcIiwgNSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImlyXFx1MDBFRGFcIiwgNSwgMiksIG5ldyBBbW9uZyhcImFkXCIsIC0xLCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiZWRcIiwgLTEsIDIpLCBuZXcgQW1vbmcoXCJpZFwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImFzZVwiLCAtMSwgMiksIG5ldyBBbW9uZyhcImllc2VcIiwgLTEsIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJhc3RlXCIsIC0xLCAyKSwgbmV3IEFtb25nKFwiaXN0ZVwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImFuXCIsIC0xLCAyKSwgbmV3IEFtb25nKFwiYWJhblwiLCAxNiwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImFyYW5cIiwgMTYsIDIpLCBuZXcgQW1vbmcoXCJpZXJhblwiLCAxNiwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcIlxcdTAwRURhblwiLCAxNiwgMiksIG5ldyBBbW9uZyhcImFyXFx1MDBFRGFuXCIsIDIwLCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiZXJcXHUwMEVEYW5cIiwgMjAsIDIpLCBuZXcgQW1vbmcoXCJpclxcdTAwRURhblwiLCAyMCwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImVuXCIsIC0xLCAxKSwgbmV3IEFtb25nKFwiYXNlblwiLCAyNCwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImllc2VuXCIsIDI0LCAyKSwgbmV3IEFtb25nKFwiYXJvblwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImllcm9uXCIsIC0xLCAyKSwgbmV3IEFtb25nKFwiYXJcXHUwMEUxblwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImVyXFx1MDBFMW5cIiwgLTEsIDIpLCBuZXcgQW1vbmcoXCJpclxcdTAwRTFuXCIsIC0xLCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiYWRvXCIsIC0xLCAyKSwgbmV3IEFtb25nKFwiaWRvXCIsIC0xLCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiYW5kb1wiLCAtMSwgMiksIG5ldyBBbW9uZyhcImllbmRvXCIsIC0xLCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiYXJcIiwgLTEsIDIpLCBuZXcgQW1vbmcoXCJlclwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImlyXCIsIC0xLCAyKSwgbmV3IEFtb25nKFwiYXNcIiwgLTEsIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJhYmFzXCIsIDM5LCAyKSwgbmV3IEFtb25nKFwiYWRhc1wiLCAzOSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImlkYXNcIiwgMzksIDIpLCBuZXcgQW1vbmcoXCJhcmFzXCIsIDM5LCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiaWVyYXNcIiwgMzksIDIpLCBuZXcgQW1vbmcoXCJcXHUwMEVEYXNcIiwgMzksIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJhclxcdTAwRURhc1wiLCA0NSwgMiksIG5ldyBBbW9uZyhcImVyXFx1MDBFRGFzXCIsIDQ1LCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiaXJcXHUwMEVEYXNcIiwgNDUsIDIpLCBuZXcgQW1vbmcoXCJlc1wiLCAtMSwgMSksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImFzZXNcIiwgNDksIDIpLCBuZXcgQW1vbmcoXCJpZXNlc1wiLCA0OSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImFiYWlzXCIsIC0xLCAyKSwgbmV3IEFtb25nKFwiYXJhaXNcIiwgLTEsIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJpZXJhaXNcIiwgLTEsIDIpLCBuZXcgQW1vbmcoXCJcXHUwMEVEYWlzXCIsIC0xLCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiYXJcXHUwMEVEYWlzXCIsIDU1LCAyKSwgbmV3IEFtb25nKFwiZXJcXHUwMEVEYWlzXCIsIDU1LCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiaXJcXHUwMEVEYWlzXCIsIDU1LCAyKSwgbmV3IEFtb25nKFwiYXNlaXNcIiwgLTEsIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJpZXNlaXNcIiwgLTEsIDIpLCBuZXcgQW1vbmcoXCJhc3RlaXNcIiwgLTEsIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJpc3RlaXNcIiwgLTEsIDIpLCBuZXcgQW1vbmcoXCJcXHUwMEUxaXNcIiwgLTEsIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJcXHUwMEU5aXNcIiwgLTEsIDEpLCBuZXcgQW1vbmcoXCJhclxcdTAwRTlpc1wiLCA2NCwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImVyXFx1MDBFOWlzXCIsIDY0LCAyKSwgbmV3IEFtb25nKFwiaXJcXHUwMEU5aXNcIiwgNjQsIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJhZG9zXCIsIC0xLCAyKSwgbmV3IEFtb25nKFwiaWRvc1wiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImFtb3NcIiwgLTEsIDIpLCBuZXcgQW1vbmcoXCJcXHUwMEUxYmFtb3NcIiwgNzAsIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJcXHUwMEUxcmFtb3NcIiwgNzAsIDIpLCBuZXcgQW1vbmcoXCJpXFx1MDBFOXJhbW9zXCIsIDcwLCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiXFx1MDBFRGFtb3NcIiwgNzAsIDIpLCBuZXcgQW1vbmcoXCJhclxcdTAwRURhbW9zXCIsIDc0LCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiZXJcXHUwMEVEYW1vc1wiLCA3NCwgMiksIG5ldyBBbW9uZyhcImlyXFx1MDBFRGFtb3NcIiwgNzQsIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJlbW9zXCIsIC0xLCAxKSwgbmV3IEFtb25nKFwiYXJlbW9zXCIsIDc4LCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiZXJlbW9zXCIsIDc4LCAyKSwgbmV3IEFtb25nKFwiaXJlbW9zXCIsIDc4LCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiXFx1MDBFMXNlbW9zXCIsIDc4LCAyKSwgbmV3IEFtb25nKFwiaVxcdTAwRTlzZW1vc1wiLCA3OCwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImltb3NcIiwgLTEsIDIpLCBuZXcgQW1vbmcoXCJhclxcdTAwRTFzXCIsIC0xLCAyKSxcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiZXJcXHUwMEUxc1wiLCAtMSwgMiksIG5ldyBBbW9uZyhcImlyXFx1MDBFMXNcIiwgLTEsIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJcXHUwMEVEc1wiLCAtMSwgMiksIG5ldyBBbW9uZyhcImFyXFx1MDBFMVwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImVyXFx1MDBFMVwiLCAtMSwgMiksIG5ldyBBbW9uZyhcImlyXFx1MDBFMVwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImFyXFx1MDBFOVwiLCAtMSwgMiksIG5ldyBBbW9uZyhcImVyXFx1MDBFOVwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcImlyXFx1MDBFOVwiLCAtMSwgMiksIG5ldyBBbW9uZyhcImlcXHUwMEYzXCIsIC0xLCAyKVxuICAgICAgICAgICAgXSxcbiAgICAgICAgICAgIGFfOSA9IFtcbiAgICAgICAgICAgICAgbmV3IEFtb25nKFwiYVwiLCAtMSwgMSksIG5ldyBBbW9uZyhcImVcIiwgLTEsIDIpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJvXCIsIC0xLCAxKSwgbmV3IEFtb25nKFwib3NcIiwgLTEsIDEpLFxuICAgICAgICAgICAgICBuZXcgQW1vbmcoXCJcXHUwMEUxXCIsIC0xLCAxKSwgbmV3IEFtb25nKFwiXFx1MDBFOVwiLCAtMSwgMiksXG4gICAgICAgICAgICAgIG5ldyBBbW9uZyhcIlxcdTAwRURcIiwgLTEsIDEpLCBuZXcgQW1vbmcoXCJcXHUwMEYzXCIsIC0xLCAxKVxuICAgICAgICAgICAgXSxcbiAgICAgICAgICAgIGdfdiA9IFsxNyxcbiAgICAgICAgICAgICAgNjUsIDE2LCAwLCAwLCAwLCAwLCAwLCAwLCAwLCAwLCAwLCAwLCAwLCAwLCAwLCAxLCAxNywgNCwgMTBcbiAgICAgICAgICAgIF0sXG4gICAgICAgICAgICBJX3AyLCBJX3AxLCBJX3BWLCBzYnAgPSBuZXcgU25vd2JhbGxQcm9ncmFtKCk7XG4gICAgICAgICAgdGhpcy5zZXRDdXJyZW50ID0gZnVuY3Rpb24od29yZCkge1xuICAgICAgICAgICAgc2JwLnNldEN1cnJlbnQod29yZCk7XG4gICAgICAgICAgfTtcbiAgICAgICAgICB0aGlzLmdldEN1cnJlbnQgPSBmdW5jdGlvbigpIHtcbiAgICAgICAgICAgIHJldHVybiBzYnAuZ2V0Q3VycmVudCgpO1xuICAgICAgICAgIH07XG5cbiAgICAgICAgICBmdW5jdGlvbiBoYWJyMSgpIHtcbiAgICAgICAgICAgIGlmIChzYnAub3V0X2dyb3VwaW5nKGdfdiwgOTcsIDI1MikpIHtcbiAgICAgICAgICAgICAgd2hpbGUgKCFzYnAuaW5fZ3JvdXBpbmcoZ192LCA5NywgMjUyKSkge1xuICAgICAgICAgICAgICAgIGlmIChzYnAuY3Vyc29yID49IHNicC5saW1pdClcbiAgICAgICAgICAgICAgICAgIHJldHVybiB0cnVlO1xuICAgICAgICAgICAgICAgIHNicC5jdXJzb3IrKztcbiAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICByZXR1cm4gdHJ1ZTtcbiAgICAgICAgICB9XG5cbiAgICAgICAgICBmdW5jdGlvbiBoYWJyMigpIHtcbiAgICAgICAgICAgIGlmIChzYnAuaW5fZ3JvdXBpbmcoZ192LCA5NywgMjUyKSkge1xuICAgICAgICAgICAgICB2YXIgdl8xID0gc2JwLmN1cnNvcjtcbiAgICAgICAgICAgICAgaWYgKGhhYnIxKCkpIHtcbiAgICAgICAgICAgICAgICBzYnAuY3Vyc29yID0gdl8xO1xuICAgICAgICAgICAgICAgIGlmICghc2JwLmluX2dyb3VwaW5nKGdfdiwgOTcsIDI1MikpXG4gICAgICAgICAgICAgICAgICByZXR1cm4gdHJ1ZTtcbiAgICAgICAgICAgICAgICB3aGlsZSAoIXNicC5vdXRfZ3JvdXBpbmcoZ192LCA5NywgMjUyKSkge1xuICAgICAgICAgICAgICAgICAgaWYgKHNicC5jdXJzb3IgPj0gc2JwLmxpbWl0KVxuICAgICAgICAgICAgICAgICAgICByZXR1cm4gdHJ1ZTtcbiAgICAgICAgICAgICAgICAgIHNicC5jdXJzb3IrKztcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgcmV0dXJuIHRydWU7XG4gICAgICAgICAgfVxuXG4gICAgICAgICAgZnVuY3Rpb24gaGFicjMoKSB7XG4gICAgICAgICAgICB2YXIgdl8xID0gc2JwLmN1cnNvcixcbiAgICAgICAgICAgICAgdl8yO1xuICAgICAgICAgICAgaWYgKGhhYnIyKCkpIHtcbiAgICAgICAgICAgICAgc2JwLmN1cnNvciA9IHZfMTtcbiAgICAgICAgICAgICAgaWYgKCFzYnAub3V0X2dyb3VwaW5nKGdfdiwgOTcsIDI1MikpXG4gICAgICAgICAgICAgICAgcmV0dXJuO1xuICAgICAgICAgICAgICB2XzIgPSBzYnAuY3Vyc29yO1xuICAgICAgICAgICAgICBpZiAoaGFicjEoKSkge1xuICAgICAgICAgICAgICAgIHNicC5jdXJzb3IgPSB2XzI7XG4gICAgICAgICAgICAgICAgaWYgKCFzYnAuaW5fZ3JvdXBpbmcoZ192LCA5NywgMjUyKSB8fCBzYnAuY3Vyc29yID49IHNicC5saW1pdClcbiAgICAgICAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgICAgICAgICBzYnAuY3Vyc29yKys7XG4gICAgICAgICAgICAgIH1cbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIElfcFYgPSBzYnAuY3Vyc29yO1xuICAgICAgICAgIH1cblxuICAgICAgICAgIGZ1bmN0aW9uIGhhYnI0KCkge1xuICAgICAgICAgICAgd2hpbGUgKCFzYnAuaW5fZ3JvdXBpbmcoZ192LCA5NywgMjUyKSkge1xuICAgICAgICAgICAgICBpZiAoc2JwLmN1cnNvciA+PSBzYnAubGltaXQpXG4gICAgICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICAgICAgICBzYnAuY3Vyc29yKys7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICB3aGlsZSAoIXNicC5vdXRfZ3JvdXBpbmcoZ192LCA5NywgMjUyKSkge1xuICAgICAgICAgICAgICBpZiAoc2JwLmN1cnNvciA+PSBzYnAubGltaXQpXG4gICAgICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICAgICAgICBzYnAuY3Vyc29yKys7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICByZXR1cm4gdHJ1ZTtcbiAgICAgICAgICB9XG5cbiAgICAgICAgICBmdW5jdGlvbiByX21hcmtfcmVnaW9ucygpIHtcbiAgICAgICAgICAgIHZhciB2XzEgPSBzYnAuY3Vyc29yO1xuICAgICAgICAgICAgSV9wViA9IHNicC5saW1pdDtcbiAgICAgICAgICAgIElfcDEgPSBJX3BWO1xuICAgICAgICAgICAgSV9wMiA9IElfcFY7XG4gICAgICAgICAgICBoYWJyMygpO1xuICAgICAgICAgICAgc2JwLmN1cnNvciA9IHZfMTtcbiAgICAgICAgICAgIGlmIChoYWJyNCgpKSB7XG4gICAgICAgICAgICAgIElfcDEgPSBzYnAuY3Vyc29yO1xuICAgICAgICAgICAgICBpZiAoaGFicjQoKSlcbiAgICAgICAgICAgICAgICBJX3AyID0gc2JwLmN1cnNvcjtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICB9XG5cbiAgICAgICAgICBmdW5jdGlvbiByX3Bvc3RsdWRlKCkge1xuICAgICAgICAgICAgdmFyIGFtb25nX3ZhcjtcbiAgICAgICAgICAgIHdoaWxlICh0cnVlKSB7XG4gICAgICAgICAgICAgIHNicC5icmEgPSBzYnAuY3Vyc29yO1xuICAgICAgICAgICAgICBhbW9uZ192YXIgPSBzYnAuZmluZF9hbW9uZyhhXzAsIDYpO1xuICAgICAgICAgICAgICBpZiAoYW1vbmdfdmFyKSB7XG4gICAgICAgICAgICAgICAgc2JwLmtldCA9IHNicC5jdXJzb3I7XG4gICAgICAgICAgICAgICAgc3dpdGNoIChhbW9uZ192YXIpIHtcbiAgICAgICAgICAgICAgICAgIGNhc2UgMTpcbiAgICAgICAgICAgICAgICAgICAgc2JwLnNsaWNlX2Zyb20oXCJhXCIpO1xuICAgICAgICAgICAgICAgICAgICBjb250aW51ZTtcbiAgICAgICAgICAgICAgICAgIGNhc2UgMjpcbiAgICAgICAgICAgICAgICAgICAgc2JwLnNsaWNlX2Zyb20oXCJlXCIpO1xuICAgICAgICAgICAgICAgICAgICBjb250aW51ZTtcbiAgICAgICAgICAgICAgICAgIGNhc2UgMzpcbiAgICAgICAgICAgICAgICAgICAgc2JwLnNsaWNlX2Zyb20oXCJpXCIpO1xuICAgICAgICAgICAgICAgICAgICBjb250aW51ZTtcbiAgICAgICAgICAgICAgICAgIGNhc2UgNDpcbiAgICAgICAgICAgICAgICAgICAgc2JwLnNsaWNlX2Zyb20oXCJvXCIpO1xuICAgICAgICAgICAgICAgICAgICBjb250aW51ZTtcbiAgICAgICAgICAgICAgICAgIGNhc2UgNTpcbiAgICAgICAgICAgICAgICAgICAgc2JwLnNsaWNlX2Zyb20oXCJ1XCIpO1xuICAgICAgICAgICAgICAgICAgICBjb250aW51ZTtcbiAgICAgICAgICAgICAgICAgIGNhc2UgNjpcbiAgICAgICAgICAgICAgICAgICAgaWYgKHNicC5jdXJzb3IgPj0gc2JwLmxpbWl0KVxuICAgICAgICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgICAgICAgICBzYnAuY3Vyc29yKys7XG4gICAgICAgICAgICAgICAgICAgIGNvbnRpbnVlO1xuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgIH1cbiAgICAgICAgICB9XG5cbiAgICAgICAgICBmdW5jdGlvbiByX1JWKCkge1xuICAgICAgICAgICAgcmV0dXJuIElfcFYgPD0gc2JwLmN1cnNvcjtcbiAgICAgICAgICB9XG5cbiAgICAgICAgICBmdW5jdGlvbiByX1IxKCkge1xuICAgICAgICAgICAgcmV0dXJuIElfcDEgPD0gc2JwLmN1cnNvcjtcbiAgICAgICAgICB9XG5cbiAgICAgICAgICBmdW5jdGlvbiByX1IyKCkge1xuICAgICAgICAgICAgcmV0dXJuIElfcDIgPD0gc2JwLmN1cnNvcjtcbiAgICAgICAgICB9XG5cbiAgICAgICAgICBmdW5jdGlvbiByX2F0dGFjaGVkX3Byb25vdW4oKSB7XG4gICAgICAgICAgICB2YXIgYW1vbmdfdmFyO1xuICAgICAgICAgICAgc2JwLmtldCA9IHNicC5jdXJzb3I7XG4gICAgICAgICAgICBpZiAoc2JwLmZpbmRfYW1vbmdfYihhXzEsIDEzKSkge1xuICAgICAgICAgICAgICBzYnAuYnJhID0gc2JwLmN1cnNvcjtcbiAgICAgICAgICAgICAgYW1vbmdfdmFyID0gc2JwLmZpbmRfYW1vbmdfYihhXzIsIDExKTtcbiAgICAgICAgICAgICAgaWYgKGFtb25nX3ZhciAmJiByX1JWKCkpXG4gICAgICAgICAgICAgICAgc3dpdGNoIChhbW9uZ192YXIpIHtcbiAgICAgICAgICAgICAgICAgIGNhc2UgMTpcbiAgICAgICAgICAgICAgICAgICAgc2JwLmJyYSA9IHNicC5jdXJzb3I7XG4gICAgICAgICAgICAgICAgICAgIHNicC5zbGljZV9mcm9tKFwiaWVuZG9cIik7XG4gICAgICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgICAgICAgY2FzZSAyOlxuICAgICAgICAgICAgICAgICAgICBzYnAuYnJhID0gc2JwLmN1cnNvcjtcbiAgICAgICAgICAgICAgICAgICAgc2JwLnNsaWNlX2Zyb20oXCJhbmRvXCIpO1xuICAgICAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgICAgICAgIGNhc2UgMzpcbiAgICAgICAgICAgICAgICAgICAgc2JwLmJyYSA9IHNicC5jdXJzb3I7XG4gICAgICAgICAgICAgICAgICAgIHNicC5zbGljZV9mcm9tKFwiYXJcIik7XG4gICAgICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgICAgICAgY2FzZSA0OlxuICAgICAgICAgICAgICAgICAgICBzYnAuYnJhID0gc2JwLmN1cnNvcjtcbiAgICAgICAgICAgICAgICAgICAgc2JwLnNsaWNlX2Zyb20oXCJlclwiKTtcbiAgICAgICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICAgICAgICBjYXNlIDU6XG4gICAgICAgICAgICAgICAgICAgIHNicC5icmEgPSBzYnAuY3Vyc29yO1xuICAgICAgICAgICAgICAgICAgICBzYnAuc2xpY2VfZnJvbShcImlyXCIpO1xuICAgICAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgICAgICAgIGNhc2UgNjpcbiAgICAgICAgICAgICAgICAgICAgc2JwLnNsaWNlX2RlbCgpO1xuICAgICAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgICAgICAgIGNhc2UgNzpcbiAgICAgICAgICAgICAgICAgICAgaWYgKHNicC5lcV9zX2IoMSwgXCJ1XCIpKVxuICAgICAgICAgICAgICAgICAgICAgIHNicC5zbGljZV9kZWwoKTtcbiAgICAgICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgfVxuICAgICAgICAgIH1cblxuICAgICAgICAgIGZ1bmN0aW9uIGhhYnI1KGEsIG4pIHtcbiAgICAgICAgICAgIGlmICghcl9SMigpKVxuICAgICAgICAgICAgICByZXR1cm4gdHJ1ZTtcbiAgICAgICAgICAgIHNicC5zbGljZV9kZWwoKTtcbiAgICAgICAgICAgIHNicC5rZXQgPSBzYnAuY3Vyc29yO1xuICAgICAgICAgICAgdmFyIGFtb25nX3ZhciA9IHNicC5maW5kX2Ftb25nX2IoYSwgbik7XG4gICAgICAgICAgICBpZiAoYW1vbmdfdmFyKSB7XG4gICAgICAgICAgICAgIHNicC5icmEgPSBzYnAuY3Vyc29yO1xuICAgICAgICAgICAgICBpZiAoYW1vbmdfdmFyID09IDEgJiYgcl9SMigpKVxuICAgICAgICAgICAgICAgIHNicC5zbGljZV9kZWwoKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgICAgICB9XG5cbiAgICAgICAgICBmdW5jdGlvbiBoYWJyNihjMSkge1xuICAgICAgICAgICAgaWYgKCFyX1IyKCkpXG4gICAgICAgICAgICAgIHJldHVybiB0cnVlO1xuICAgICAgICAgICAgc2JwLnNsaWNlX2RlbCgpO1xuICAgICAgICAgICAgc2JwLmtldCA9IHNicC5jdXJzb3I7XG4gICAgICAgICAgICBpZiAoc2JwLmVxX3NfYigyLCBjMSkpIHtcbiAgICAgICAgICAgICAgc2JwLmJyYSA9IHNicC5jdXJzb3I7XG4gICAgICAgICAgICAgIGlmIChyX1IyKCkpXG4gICAgICAgICAgICAgICAgc2JwLnNsaWNlX2RlbCgpO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICAgIH1cblxuICAgICAgICAgIGZ1bmN0aW9uIHJfc3RhbmRhcmRfc3VmZml4KCkge1xuICAgICAgICAgICAgdmFyIGFtb25nX3ZhcjtcbiAgICAgICAgICAgIHNicC5rZXQgPSBzYnAuY3Vyc29yO1xuICAgICAgICAgICAgYW1vbmdfdmFyID0gc2JwLmZpbmRfYW1vbmdfYihhXzYsIDQ2KTtcbiAgICAgICAgICAgIGlmIChhbW9uZ192YXIpIHtcbiAgICAgICAgICAgICAgc2JwLmJyYSA9IHNicC5jdXJzb3I7XG4gICAgICAgICAgICAgIHN3aXRjaCAoYW1vbmdfdmFyKSB7XG4gICAgICAgICAgICAgICAgY2FzZSAxOlxuICAgICAgICAgICAgICAgICAgaWYgKCFyX1IyKCkpXG4gICAgICAgICAgICAgICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgICAgICAgICAgICAgIHNicC5zbGljZV9kZWwoKTtcbiAgICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgICAgIGNhc2UgMjpcbiAgICAgICAgICAgICAgICAgIGlmIChoYWJyNihcImljXCIpKVxuICAgICAgICAgICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgICAgICBjYXNlIDM6XG4gICAgICAgICAgICAgICAgICBpZiAoIXJfUjIoKSlcbiAgICAgICAgICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICAgICAgICAgICAgc2JwLnNsaWNlX2Zyb20oXCJsb2dcIik7XG4gICAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgICAgICBjYXNlIDQ6XG4gICAgICAgICAgICAgICAgICBpZiAoIXJfUjIoKSlcbiAgICAgICAgICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICAgICAgICAgICAgc2JwLnNsaWNlX2Zyb20oXCJ1XCIpO1xuICAgICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICAgICAgY2FzZSA1OlxuICAgICAgICAgICAgICAgICAgaWYgKCFyX1IyKCkpXG4gICAgICAgICAgICAgICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgICAgICAgICAgICAgIHNicC5zbGljZV9mcm9tKFwiZW50ZVwiKTtcbiAgICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgICAgIGNhc2UgNjpcbiAgICAgICAgICAgICAgICAgIGlmICghcl9SMSgpKVxuICAgICAgICAgICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgICAgICAgICAgICBzYnAuc2xpY2VfZGVsKCk7XG4gICAgICAgICAgICAgICAgICBzYnAua2V0ID0gc2JwLmN1cnNvcjtcbiAgICAgICAgICAgICAgICAgIGFtb25nX3ZhciA9IHNicC5maW5kX2Ftb25nX2IoYV8zLCA0KTtcbiAgICAgICAgICAgICAgICAgIGlmIChhbW9uZ192YXIpIHtcbiAgICAgICAgICAgICAgICAgICAgc2JwLmJyYSA9IHNicC5jdXJzb3I7XG4gICAgICAgICAgICAgICAgICAgIGlmIChyX1IyKCkpIHtcbiAgICAgICAgICAgICAgICAgICAgICBzYnAuc2xpY2VfZGVsKCk7XG4gICAgICAgICAgICAgICAgICAgICAgaWYgKGFtb25nX3ZhciA9PSAxKSB7XG4gICAgICAgICAgICAgICAgICAgICAgICBzYnAua2V0ID0gc2JwLmN1cnNvcjtcbiAgICAgICAgICAgICAgICAgICAgICAgIGlmIChzYnAuZXFfc19iKDIsIFwiYXRcIikpIHtcbiAgICAgICAgICAgICAgICAgICAgICAgICAgc2JwLmJyYSA9IHNicC5jdXJzb3I7XG4gICAgICAgICAgICAgICAgICAgICAgICAgIGlmIChyX1IyKCkpXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgc2JwLnNsaWNlX2RlbCgpO1xuICAgICAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICAgICAgY2FzZSA3OlxuICAgICAgICAgICAgICAgICAgaWYgKGhhYnI1KGFfNCwgMykpXG4gICAgICAgICAgICAgICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgICAgIGNhc2UgODpcbiAgICAgICAgICAgICAgICAgIGlmIChoYWJyNShhXzUsIDMpKVxuICAgICAgICAgICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgICAgICBjYXNlIDk6XG4gICAgICAgICAgICAgICAgICBpZiAoaGFicjYoXCJhdFwiKSlcbiAgICAgICAgICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgcmV0dXJuIHRydWU7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgICAgfVxuXG4gICAgICAgICAgZnVuY3Rpb24gcl95X3ZlcmJfc3VmZml4KCkge1xuICAgICAgICAgICAgdmFyIGFtb25nX3Zhciwgdl8xO1xuICAgICAgICAgICAgaWYgKHNicC5jdXJzb3IgPj0gSV9wVikge1xuICAgICAgICAgICAgICB2XzEgPSBzYnAubGltaXRfYmFja3dhcmQ7XG4gICAgICAgICAgICAgIHNicC5saW1pdF9iYWNrd2FyZCA9IElfcFY7XG4gICAgICAgICAgICAgIHNicC5rZXQgPSBzYnAuY3Vyc29yO1xuICAgICAgICAgICAgICBhbW9uZ192YXIgPSBzYnAuZmluZF9hbW9uZ19iKGFfNywgMTIpO1xuICAgICAgICAgICAgICBzYnAubGltaXRfYmFja3dhcmQgPSB2XzE7XG4gICAgICAgICAgICAgIGlmIChhbW9uZ192YXIpIHtcbiAgICAgICAgICAgICAgICBzYnAuYnJhID0gc2JwLmN1cnNvcjtcbiAgICAgICAgICAgICAgICBpZiAoYW1vbmdfdmFyID09IDEpIHtcbiAgICAgICAgICAgICAgICAgIGlmICghc2JwLmVxX3NfYigxLCBcInVcIikpXG4gICAgICAgICAgICAgICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgICAgICAgICAgICAgIHNicC5zbGljZV9kZWwoKTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgcmV0dXJuIHRydWU7XG4gICAgICAgICAgICAgIH1cbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgICAgICB9XG5cbiAgICAgICAgICBmdW5jdGlvbiByX3ZlcmJfc3VmZml4KCkge1xuICAgICAgICAgICAgdmFyIGFtb25nX3Zhciwgdl8xLCB2XzIsIHZfMztcbiAgICAgICAgICAgIGlmIChzYnAuY3Vyc29yID49IElfcFYpIHtcbiAgICAgICAgICAgICAgdl8xID0gc2JwLmxpbWl0X2JhY2t3YXJkO1xuICAgICAgICAgICAgICBzYnAubGltaXRfYmFja3dhcmQgPSBJX3BWO1xuICAgICAgICAgICAgICBzYnAua2V0ID0gc2JwLmN1cnNvcjtcbiAgICAgICAgICAgICAgYW1vbmdfdmFyID0gc2JwLmZpbmRfYW1vbmdfYihhXzgsIDk2KTtcbiAgICAgICAgICAgICAgc2JwLmxpbWl0X2JhY2t3YXJkID0gdl8xO1xuICAgICAgICAgICAgICBpZiAoYW1vbmdfdmFyKSB7XG4gICAgICAgICAgICAgICAgc2JwLmJyYSA9IHNicC5jdXJzb3I7XG4gICAgICAgICAgICAgICAgc3dpdGNoIChhbW9uZ192YXIpIHtcbiAgICAgICAgICAgICAgICAgIGNhc2UgMTpcbiAgICAgICAgICAgICAgICAgICAgdl8yID0gc2JwLmxpbWl0IC0gc2JwLmN1cnNvcjtcbiAgICAgICAgICAgICAgICAgICAgaWYgKHNicC5lcV9zX2IoMSwgXCJ1XCIpKSB7XG4gICAgICAgICAgICAgICAgICAgICAgdl8zID0gc2JwLmxpbWl0IC0gc2JwLmN1cnNvcjtcbiAgICAgICAgICAgICAgICAgICAgICBpZiAoc2JwLmVxX3NfYigxLCBcImdcIikpXG4gICAgICAgICAgICAgICAgICAgICAgICBzYnAuY3Vyc29yID0gc2JwLmxpbWl0IC0gdl8zO1xuICAgICAgICAgICAgICAgICAgICAgIGVsc2VcbiAgICAgICAgICAgICAgICAgICAgICAgIHNicC5jdXJzb3IgPSBzYnAubGltaXQgLSB2XzI7XG4gICAgICAgICAgICAgICAgICAgIH0gZWxzZVxuICAgICAgICAgICAgICAgICAgICAgIHNicC5jdXJzb3IgPSBzYnAubGltaXQgLSB2XzI7XG4gICAgICAgICAgICAgICAgICAgIHNicC5icmEgPSBzYnAuY3Vyc29yO1xuICAgICAgICAgICAgICAgICAgY2FzZSAyOlxuICAgICAgICAgICAgICAgICAgICBzYnAuc2xpY2VfZGVsKCk7XG4gICAgICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgfVxuICAgICAgICAgIH1cblxuICAgICAgICAgIGZ1bmN0aW9uIHJfcmVzaWR1YWxfc3VmZml4KCkge1xuICAgICAgICAgICAgdmFyIGFtb25nX3Zhciwgdl8xO1xuICAgICAgICAgICAgc2JwLmtldCA9IHNicC5jdXJzb3I7XG4gICAgICAgICAgICBhbW9uZ192YXIgPSBzYnAuZmluZF9hbW9uZ19iKGFfOSwgOCk7XG4gICAgICAgICAgICBpZiAoYW1vbmdfdmFyKSB7XG4gICAgICAgICAgICAgIHNicC5icmEgPSBzYnAuY3Vyc29yO1xuICAgICAgICAgICAgICBzd2l0Y2ggKGFtb25nX3Zhcikge1xuICAgICAgICAgICAgICAgIGNhc2UgMTpcbiAgICAgICAgICAgICAgICAgIGlmIChyX1JWKCkpXG4gICAgICAgICAgICAgICAgICAgIHNicC5zbGljZV9kZWwoKTtcbiAgICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgICAgIGNhc2UgMjpcbiAgICAgICAgICAgICAgICAgIGlmIChyX1JWKCkpIHtcbiAgICAgICAgICAgICAgICAgICAgc2JwLnNsaWNlX2RlbCgpO1xuICAgICAgICAgICAgICAgICAgICBzYnAua2V0ID0gc2JwLmN1cnNvcjtcbiAgICAgICAgICAgICAgICAgICAgaWYgKHNicC5lcV9zX2IoMSwgXCJ1XCIpKSB7XG4gICAgICAgICAgICAgICAgICAgICAgc2JwLmJyYSA9IHNicC5jdXJzb3I7XG4gICAgICAgICAgICAgICAgICAgICAgdl8xID0gc2JwLmxpbWl0IC0gc2JwLmN1cnNvcjtcbiAgICAgICAgICAgICAgICAgICAgICBpZiAoc2JwLmVxX3NfYigxLCBcImdcIikpIHtcbiAgICAgICAgICAgICAgICAgICAgICAgIHNicC5jdXJzb3IgPSBzYnAubGltaXQgLSB2XzE7XG4gICAgICAgICAgICAgICAgICAgICAgICBpZiAocl9SVigpKVxuICAgICAgICAgICAgICAgICAgICAgICAgICBzYnAuc2xpY2VfZGVsKCk7XG4gICAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgfVxuICAgICAgICAgIH1cbiAgICAgICAgICB0aGlzLnN0ZW0gPSBmdW5jdGlvbigpIHtcbiAgICAgICAgICAgIHZhciB2XzEgPSBzYnAuY3Vyc29yO1xuICAgICAgICAgICAgcl9tYXJrX3JlZ2lvbnMoKTtcbiAgICAgICAgICAgIHNicC5saW1pdF9iYWNrd2FyZCA9IHZfMTtcbiAgICAgICAgICAgIHNicC5jdXJzb3IgPSBzYnAubGltaXQ7XG4gICAgICAgICAgICByX2F0dGFjaGVkX3Byb25vdW4oKTtcbiAgICAgICAgICAgIHNicC5jdXJzb3IgPSBzYnAubGltaXQ7XG4gICAgICAgICAgICBpZiAoIXJfc3RhbmRhcmRfc3VmZml4KCkpIHtcbiAgICAgICAgICAgICAgc2JwLmN1cnNvciA9IHNicC5saW1pdDtcbiAgICAgICAgICAgICAgaWYgKCFyX3lfdmVyYl9zdWZmaXgoKSkge1xuICAgICAgICAgICAgICAgIHNicC5jdXJzb3IgPSBzYnAubGltaXQ7XG4gICAgICAgICAgICAgICAgcl92ZXJiX3N1ZmZpeCgpO1xuICAgICAgICAgICAgICB9XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICBzYnAuY3Vyc29yID0gc2JwLmxpbWl0O1xuICAgICAgICAgICAgcl9yZXNpZHVhbF9zdWZmaXgoKTtcbiAgICAgICAgICAgIHNicC5jdXJzb3IgPSBzYnAubGltaXRfYmFja3dhcmQ7XG4gICAgICAgICAgICByX3Bvc3RsdWRlKCk7XG4gICAgICAgICAgICByZXR1cm4gdHJ1ZTtcbiAgICAgICAgICB9XG4gICAgICAgIH07XG5cbiAgICAgIC8qIGFuZCByZXR1cm4gYSBmdW5jdGlvbiB0aGF0IHN0ZW1zIGEgd29yZCBmb3IgdGhlIGN1cnJlbnQgbG9jYWxlICovXG4gICAgICByZXR1cm4gZnVuY3Rpb24odG9rZW4pIHtcbiAgICAgICAgLy8gZm9yIGx1bnIgdmVyc2lvbiAyXG4gICAgICAgIGlmICh0eXBlb2YgdG9rZW4udXBkYXRlID09PSBcImZ1bmN0aW9uXCIpIHtcbiAgICAgICAgICByZXR1cm4gdG9rZW4udXBkYXRlKGZ1bmN0aW9uKHdvcmQpIHtcbiAgICAgICAgICAgIHN0LnNldEN1cnJlbnQod29yZCk7XG4gICAgICAgICAgICBzdC5zdGVtKCk7XG4gICAgICAgICAgICByZXR1cm4gc3QuZ2V0Q3VycmVudCgpO1xuICAgICAgICAgIH0pXG4gICAgICAgIH0gZWxzZSB7IC8vIGZvciBsdW5yIHZlcnNpb24gPD0gMVxuICAgICAgICAgIHN0LnNldEN1cnJlbnQodG9rZW4pO1xuICAgICAgICAgIHN0LnN0ZW0oKTtcbiAgICAgICAgICByZXR1cm4gc3QuZ2V0Q3VycmVudCgpO1xuICAgICAgICB9XG4gICAgICB9XG4gICAgfSkoKTtcblxuICAgIGx1bnIuUGlwZWxpbmUucmVnaXN0ZXJGdW5jdGlvbihsdW5yLmVzLnN0ZW1tZXIsICdzdGVtbWVyLWVzJyk7XG5cbiAgICBsdW5yLmVzLnN0b3BXb3JkRmlsdGVyID0gbHVuci5nZW5lcmF0ZVN0b3BXb3JkRmlsdGVyKCdhIGFsIGFsZ28gYWxndW5hcyBhbGd1bm9zIGFudGUgYW50ZXMgY29tbyBjb24gY29udHJhIGN1YWwgY3VhbmRvIGRlIGRlbCBkZXNkZSBkb25kZSBkdXJhbnRlIGUgZWwgZWxsYSBlbGxhcyBlbGxvcyBlbiBlbnRyZSBlcmEgZXJhaXMgZXJhbiBlcmFzIGVyZXMgZXMgZXNhIGVzYXMgZXNlIGVzbyBlc29zIGVzdGEgZXN0YWJhIGVzdGFiYWlzIGVzdGFiYW4gZXN0YWJhcyBlc3RhZCBlc3RhZGEgZXN0YWRhcyBlc3RhZG8gZXN0YWRvcyBlc3RhbW9zIGVzdGFuZG8gZXN0YXIgZXN0YXJlbW9zIGVzdGFyw6EgZXN0YXLDoW4gZXN0YXLDoXMgZXN0YXLDqSBlc3RhcsOpaXMgZXN0YXLDrWEgZXN0YXLDrWFpcyBlc3RhcsOtYW1vcyBlc3RhcsOtYW4gZXN0YXLDrWFzIGVzdGFzIGVzdGUgZXN0ZW1vcyBlc3RvIGVzdG9zIGVzdG95IGVzdHV2ZSBlc3R1dmllcmEgZXN0dXZpZXJhaXMgZXN0dXZpZXJhbiBlc3R1dmllcmFzIGVzdHV2aWVyb24gZXN0dXZpZXNlIGVzdHV2aWVzZWlzIGVzdHV2aWVzZW4gZXN0dXZpZXNlcyBlc3R1dmltb3MgZXN0dXZpc3RlIGVzdHV2aXN0ZWlzIGVzdHV2acOpcmFtb3MgZXN0dXZpw6lzZW1vcyBlc3R1dm8gZXN0w6EgZXN0w6FiYW1vcyBlc3TDoWlzIGVzdMOhbiBlc3TDoXMgZXN0w6kgZXN0w6lpcyBlc3TDqW4gZXN0w6lzIGZ1ZSBmdWVyYSBmdWVyYWlzIGZ1ZXJhbiBmdWVyYXMgZnVlcm9uIGZ1ZXNlIGZ1ZXNlaXMgZnVlc2VuIGZ1ZXNlcyBmdWkgZnVpbW9zIGZ1aXN0ZSBmdWlzdGVpcyBmdcOpcmFtb3MgZnXDqXNlbW9zIGhhIGhhYmlkYSBoYWJpZGFzIGhhYmlkbyBoYWJpZG9zIGhhYmllbmRvIGhhYnJlbW9zIGhhYnLDoSBoYWJyw6FuIGhhYnLDoXMgaGFicsOpIGhhYnLDqWlzIGhhYnLDrWEgaGFicsOtYWlzIGhhYnLDrWFtb3MgaGFicsOtYW4gaGFicsOtYXMgaGFiw6lpcyBoYWLDrWEgaGFiw61haXMgaGFiw61hbW9zIGhhYsOtYW4gaGFiw61hcyBoYW4gaGFzIGhhc3RhIGhheSBoYXlhIGhheWFtb3MgaGF5YW4gaGF5YXMgaGF5w6FpcyBoZSBoZW1vcyBodWJlIGh1YmllcmEgaHViaWVyYWlzIGh1YmllcmFuIGh1YmllcmFzIGh1Ymllcm9uIGh1Ymllc2UgaHViaWVzZWlzIGh1Ymllc2VuIGh1Ymllc2VzIGh1Ymltb3MgaHViaXN0ZSBodWJpc3RlaXMgaHViacOpcmFtb3MgaHViacOpc2Vtb3MgaHVibyBsYSBsYXMgbGUgbGVzIGxvIGxvcyBtZSBtaSBtaXMgbXVjaG8gbXVjaG9zIG11eSBtw6FzIG3DrSBtw61hIG3DrWFzIG3DrW8gbcOtb3MgbmFkYSBuaSBubyBub3Mgbm9zb3RyYXMgbm9zb3Ryb3MgbnVlc3RyYSBudWVzdHJhcyBudWVzdHJvIG51ZXN0cm9zIG8gb3Mgb3RyYSBvdHJhcyBvdHJvIG90cm9zIHBhcmEgcGVybyBwb2NvIHBvciBwb3JxdWUgcXVlIHF1aWVuIHF1aWVuZXMgcXXDqSBzZSBzZWEgc2VhbW9zIHNlYW4gc2VhcyBzZXJlbW9zIHNlcsOhIHNlcsOhbiBzZXLDoXMgc2Vyw6kgc2Vyw6lpcyBzZXLDrWEgc2Vyw61haXMgc2Vyw61hbW9zIHNlcsOtYW4gc2Vyw61hcyBzZcOhaXMgc2lkbyBzaWVuZG8gc2luIHNvYnJlIHNvaXMgc29tb3Mgc29uIHNveSBzdSBzdXMgc3V5YSBzdXlhcyBzdXlvIHN1eW9zIHPDrSB0YW1iacOpbiB0YW50byB0ZSB0ZW5kcmVtb3MgdGVuZHLDoSB0ZW5kcsOhbiB0ZW5kcsOhcyB0ZW5kcsOpIHRlbmRyw6lpcyB0ZW5kcsOtYSB0ZW5kcsOtYWlzIHRlbmRyw61hbW9zIHRlbmRyw61hbiB0ZW5kcsOtYXMgdGVuZWQgdGVuZW1vcyB0ZW5nYSB0ZW5nYW1vcyB0ZW5nYW4gdGVuZ2FzIHRlbmdvIHRlbmfDoWlzIHRlbmlkYSB0ZW5pZGFzIHRlbmlkbyB0ZW5pZG9zIHRlbmllbmRvIHRlbsOpaXMgdGVuw61hIHRlbsOtYWlzIHRlbsOtYW1vcyB0ZW7DrWFuIHRlbsOtYXMgdGkgdGllbmUgdGllbmVuIHRpZW5lcyB0b2RvIHRvZG9zIHR1IHR1cyB0dXZlIHR1dmllcmEgdHV2aWVyYWlzIHR1dmllcmFuIHR1dmllcmFzIHR1dmllcm9uIHR1dmllc2UgdHV2aWVzZWlzIHR1dmllc2VuIHR1dmllc2VzIHR1dmltb3MgdHV2aXN0ZSB0dXZpc3RlaXMgdHV2acOpcmFtb3MgdHV2acOpc2Vtb3MgdHV2byB0dXlhIHR1eWFzIHR1eW8gdHV5b3MgdMO6IHVuIHVuYSB1bm8gdW5vcyB2b3NvdHJhcyB2b3NvdHJvcyB2dWVzdHJhIHZ1ZXN0cmFzIHZ1ZXN0cm8gdnVlc3Ryb3MgeSB5YSB5byDDqWwgw6lyYW1vcycuc3BsaXQoJyAnKSk7XG5cbiAgICBsdW5yLlBpcGVsaW5lLnJlZ2lzdGVyRnVuY3Rpb24obHVuci5lcy5zdG9wV29yZEZpbHRlciwgJ3N0b3BXb3JkRmlsdGVyLWVzJyk7XG4gIH07XG59KSkiLCJsZXQgcmggPSBnbG9iYWwucmhcclxubGV0IGx1bnJsYW5nID0gcmVxdWlyZSgnLi4vLi4vbm9kZV9tb2R1bGVzL2x1bnItbGFuZ3VhZ2VzL2x1bnIuZXMnKVxyXG5yaC5fLmV4cG9ydHMoIGx1bnJsYW5nKSJdfQ==
