const D=require('docx'); const fs=require('fs');
const L=require('../doc_lib.js');
const {Document,Packer,Paragraph,TextRun,AlignmentType,LevelFormat}=D;
const {P,H1,H2,H3,H4,BULLET,NUMLIST,tableBlock,FONT,SZP,TSZ,BLACK}=L;
const {ImageRun}=D;
const F='Times New Roman';
function figBlock(n,title,file,note,sizes){
  const [pw,ph]=sizes[file]; const W=600, Hh=Math.round(W*ph/pw);
  return [
    new Paragraph({children:[new TextRun({text:`Figure ${n}`,font:F,size:24,bold:true,color:'000000'})],spacing:{before:240,after:0,line:240}}),
    new Paragraph({children:[new TextRun({text:title,font:F,size:24,italics:true,color:'000000'})],spacing:{before:0,after:120,line:240}}),
    new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:100},children:[new ImageRun({type:'png',data:fs.readFileSync(`v5/fig/${file}.png`),transformation:{width:W,height:Hh}})]}),
    new Paragraph({children:[new TextRun({text:'Note. ',font:F,size:20,italics:true,color:'000000'}),new TextRun({text:note,font:F,size:20,color:'000000'})],alignment:AlignmentType.JUSTIFIED,spacing:{before:60,after:240,line:240}}),
  ];
}

const T=require('./tables_final.json');
const SZ=require('./figsizes.json');
const ch4=require('./ch4.json'), ch56=require('./ch56.json');
const byNum={}; T.forEach(t=>byNum[t.num]=t);

function render(blocks){
  const out=[];
  for(const b of blocks){
    switch(b.k){
      case 'h1': out.push(H1(b.t)); break;
      case 'h2': out.push(H2(b.t)); break;
      case 'h3': out.push(H3(b.t)); break;
      case 'h4': out.push(H4(b.t)); break;
      case 'p':  out.push(P(b.t)); break;
      case 'bul': out.push(BULLET(b.t)); break;
      case 'num': out.push(NUMLIST(b.t, b.ref)); break;
      case 'table': {
        const spec=Object.assign({}, byNum[b.n]);
        if(b.t) spec.title=b.t;
        if(!spec) throw new Error('missing table '+b.n);
        out.push(...tableBlock(spec)); break;
      }
      case 'fig': out.push(...figBlock(b.n, b.t, b.f, b.note, SZ)); break;
      default: throw new Error('unknown block '+b.k);
    }
  }
  return out;
}

const num=(ref)=>({reference:ref,levels:[{level:0,format:LevelFormat.DECIMAL,text:'%1.',
  alignment:AlignmentType.START,style:{paragraph:{indent:{left:720,hanging:360}}}}]});

const doc=new Document({
  creator:'Mercy Sangura', title:'Chapters Four to Six',
  description:'Results, Discussion, Conclusions and Recommendations',
  styles:{default:{document:{run:{font:'Times New Roman',size:24,color:'000000'},
                             paragraph:{spacing:{line:360}}}}},
  numbering:{config:[
    {reference:'bul',levels:[{level:0,format:LevelFormat.BULLET,text:'•',
      alignment:AlignmentType.START,style:{paragraph:{indent:{left:720,hanging:360}}}}]},
    num('n1'),num('n2'),num('n3')]},
  sections:[{
    properties:{page:{size:{width:11906,height:16838},
      margin:{top:1440,right:1440,bottom:1440,left:1440}}},
    children:[...render(ch4), ...render(ch56)],
  }],
});
Packer.toBuffer(doc).then(b=>{
  fs.writeFileSync('v5/Chapters_Four_to_Six.docx',b);
  console.log('written', (b.length/1024).toFixed(0)+' KB');
});
