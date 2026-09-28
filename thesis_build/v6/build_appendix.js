const D=require('docx'); const fs=require('fs');
const L=require('../doc_lib.js');
const {Document,Packer,Paragraph,TextRun,AlignmentType}=D;
const {P,H1,H2,tableBlock}=L;
const A=require('./appendix.json');
let n=0;
const children=[];
for(const b of A){
  switch(b.k){
    case 'h1': children.push(H1(b.t)); break;
    case 'h2': children.push(H2(b.t)); break;
    case 'p':  children.push(P(b.t)); break;
    case 'rawtable': {
      n++;
      children.push(...tableBlock({num:'A'+n, title:b.title, headers:b.headers,
                                   rows:b.rows, widths:b.widths, note:b.note}));
      break;
    }
  }
}
const doc=new Document({
  creator:'Mercy Sangura', title:'Appendix A: SPSS Output',
  styles:{default:{document:{run:{font:'Times New Roman',size:24,color:'000000'},
                             paragraph:{spacing:{line:360}}}}},
  sections:[{properties:{page:{size:{width:11906,height:16838},
    margin:{top:1440,right:1440,bottom:1440,left:1440}}}, children}],
});
Packer.toBuffer(doc).then(b=>{
  fs.writeFileSync('v6/Appendix_A_SPSS_Output.docx',b);
  console.log('written', (b.length/1024).toFixed(0)+' KB;', n, 'output tables');
});
